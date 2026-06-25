"""LLM 管理端诊断：脱敏展示、今日统计、网关探活"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import LLM_API_KEY, LLM_ENABLED, LLM_GATEWAY_URL, LLM_MODEL, LLM_TIMEOUT_SEC
from llm_service import llm_enabled
from models import LlmCallLog


def _today_start() -> datetime:
    now = datetime.utcnow()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def mask_api_key(key: str) -> str:
    if not key:
        return "（未配置）"
    k = str(key).strip()
    if len(k) <= 8:
        return "****"
    return f"{k[:4]}…{k[-4:]}"


def gateway_endpoint_display(url: str) -> str:
    if not url:
        return "（未配置）"
    base = url.rstrip("/")
    if not base.endswith("/chat/completions"):
        base = base + "/v1/chat/completions"
    return base


def gateway_host(url: str) -> str:
    if not url:
        return ""
    try:
        return urlparse(url.rstrip("/")).netloc or url
    except Exception:
        return url


def build_config_snapshot() -> Dict[str, Any]:
    return {
        "llm_enabled_flag": LLM_ENABLED,
        "gateway_url_set": bool(LLM_GATEWAY_URL),
        "gateway_host": gateway_host(LLM_GATEWAY_URL),
        "gateway_endpoint": gateway_endpoint_display(LLM_GATEWAY_URL),
        "api_key_set": bool(LLM_API_KEY),
        "api_key_hint": mask_api_key(LLM_API_KEY),
        "model": LLM_MODEL,
        "timeout_sec": LLM_TIMEOUT_SEC,
        "runtime_enabled": llm_enabled(),
    }


def today_stats(db: Session) -> Dict[str, int]:
    start = _today_start()
    rows = (
        db.query(LlmCallLog.status, func.count(LlmCallLog.id))
        .filter(LlmCallLog.created_at >= start)
        .group_by(LlmCallLog.status)
        .all()
    )
    stats = {s: int(n) for s, n in rows}
    for key in ("success", "error", "quota", "disabled", "fallback"):
        stats.setdefault(key, 0)
    stats["total"] = sum(stats.values())
    return stats


def recent_logs(db: Session, limit: int = 30) -> List[LlmCallLog]:
    return (
        db.query(LlmCallLog)
        .order_by(LlmCallLog.id.desc())
        .limit(limit)
        .all()
    )


def last_error_message(db: Session) -> Optional[str]:
    row = (
        db.query(LlmCallLog)
        .filter(LlmCallLog.status.in_(("error", "quota", "disabled")))
        .order_by(LlmCallLog.id.desc())
        .first()
    )
    if not row:
        return None
    parts = [row.status]
    if row.route:
        parts.append(row.route)
    if row.message:
        parts.append(row.message)
    return " · ".join(parts)


def route_stats_today(db: Session, limit: int = 12) -> List[Dict[str, Any]]:
    start = _today_start()
    rows = (
        db.query(
            LlmCallLog.route,
            LlmCallLog.status,
            func.count(LlmCallLog.id),
        )
        .filter(LlmCallLog.created_at >= start)
        .group_by(LlmCallLog.route, LlmCallLog.status)
        .all()
    )
    by_route: Dict[str, Dict[str, int]] = {}
    for route, status, count in rows:
        bucket = by_route.setdefault(route, {"success": 0, "error": 0, "other": 0, "total": 0})
        c = int(count)
        bucket["total"] += c
        if status == "success":
            bucket["success"] += c
        elif status == "error":
            bucket["error"] += c
        else:
            bucket["other"] += c
    items = [
        {"route": route, **counts}
        for route, counts in by_route.items()
    ]
    items.sort(key=lambda x: x["total"], reverse=True)
    return items[:limit]


def diagnose_runtime(db: Session) -> List[str]:
    """根据配置 + 今日日志给出排查提示（不含密钥）。"""
    tips: List[str] = []
    cfg = build_config_snapshot()
    stats = today_stats(db)

    if not cfg["llm_enabled_flag"]:
        tips.append("LLM_ENABLED=false：在服务器 /opt/sandtable/server/.env 设为 true 后 systemctl restart sandtable")
    if not cfg["gateway_url_set"]:
        tips.append("未配置 LLM_GATEWAY_URL（DeepSeek 示例：https://api.deepseek.com）")
    if not cfg["api_key_set"]:
        tips.append("未配置 LLM_API_KEY")
    if cfg["llm_enabled_flag"] and cfg["gateway_url_set"] and cfg["api_key_set"] and not cfg["runtime_enabled"]:
        tips.append("配置项齐全但 runtime_enabled=false，请检查 .env 是否有多余空格或引号")

    last_err = last_error_message(db)
    if last_err and "402" in last_err:
        tips.insert(0, "DeepSeek 返回 HTTP 402：账户需充值（platform.deepseek.com → 用量/充值），与 sandtable 配置无关")

    if stats.get("quota", 0) > 0:
        tips.append(f"今日已有 {stats['quota']} 次配额拦截，可调高 LLM_DAILY_CAP / LLM_USER_DAILY_CAP 或次日再试")

    if stats.get("error", 0) > 0 and stats.get("success", 0) == 0:
        tips.append("今日 LLM 调用全部失败：点「网关探活」看 HTTP/连接错误；常见为 Key 无效或服务器无法访问公网")

    if stats.get("disabled", 0) > 0:
        tips.append("存在 disabled 日志：可能 LLM 曾关闭，或 readonly 账号未开 LLM_READONLY_ENABLED")

    if not tips and cfg["runtime_enabled"] and stats.get("success", 0) > 0:
        tips.append("LLM 运行正常；若页面仍显示规则版，硬刷新并清 intel_briefing_cache")

    if not tips:
        tips.append("点「网关探活」确认外网连通；通过后刷新档案/情报页验证 source=llm")

    return tips


async def probe_gateway(db: Optional[Session] = None, auth_user=None) -> Dict[str, Any]:
    """最小 chat/completions 探活；admin 专用，不走业务配额。"""
    import time

    from llm_audit import estimate_tokens, log_llm_call

    if not LLM_ENABLED:
        return {"ok": False, "latency_ms": 0, "error": "LLM_ENABLED=false", "hint": "修改 .env 后重启 sandtable"}
    if not LLM_GATEWAY_URL or not LLM_API_KEY:
        return {"ok": False, "latency_ms": 0, "error": "网关或 API Key 未配置", "hint": "bash deploy/point-config-llm-cloud.sh"}

    url = gateway_endpoint_display(LLM_GATEWAY_URL)
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "你是探活助手，只回复 OK"},
            {"role": "user", "content": "ping"},
        ],
        "max_tokens": 8,
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    t0 = time.perf_counter()

    try:
        timeout = min(float(LLM_TIMEOUT_SEC), 20.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            latency = int((time.perf_counter() - t0) * 1000)
            if resp.status_code >= 400:
                body = resp.text[:240]
                if db is not None:
                    log_llm_call(
                        db,
                        user=auth_user,
                        route="admin.probe",
                        status="error",
                        latency_ms=latency,
                        tokens_est=0,
                        message=f"HTTP {resp.status_code}: {body[:180]}",
                    )
                hint = "401/403 多为 Key 错误；404 检查 GATEWAY_URL 是否含 /v1/chat/completions"
                if resp.status_code == 402:
                    hint = "DeepSeek 账户余额不足或未开通付费：登录 platform.deepseek.com 充值后再探活"
                return {
                    "ok": False,
                    "latency_ms": latency,
                    "http_status": resp.status_code,
                    "error": body or f"HTTP {resp.status_code}",
                    "hint": hint,
                }
            data = resp.json()
            text = data["choices"][0]["message"]["content"].strip()
            if db is not None:
                log_llm_call(
                    db,
                    user=auth_user,
                    route="admin.probe",
                    status="success",
                    latency_ms=latency,
                    tokens_est=estimate_tokens("ping", "ping", text),
                    message=text[:120],
                )
            return {
                "ok": True,
                "latency_ms": latency,
                "http_status": resp.status_code,
                "sample": text[:80],
                "model": LLM_MODEL,
                "endpoint": url,
            }
    except httpx.ConnectError as exc:
        latency = int((time.perf_counter() - t0) * 1000)
        msg = str(exc)[:200]
        if db is not None:
            log_llm_call(db, user=auth_user, route="admin.probe", status="error", latency_ms=latency, message=msg)
        return {
            "ok": False,
            "latency_ms": latency,
            "error": f"连接失败: {msg}",
            "hint": "云服务器需能访问公网；检查安全组/防火墙/DNS",
        }
    except Exception as exc:
        latency = int((time.perf_counter() - t0) * 1000)
        msg = str(exc)[:200]
        if db is not None:
            log_llm_call(db, user=auth_user, route="admin.probe", status="error", latency_ms=latency, message=msg)
        return {"ok": False, "latency_ms": latency, "error": msg, "hint": "查看下方审计日志 message 列"}
