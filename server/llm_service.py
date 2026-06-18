"""
M3/M4 LLM 中台
- LLM_ENABLED=false 时一律返回 None，由调用方降级 M2 规则版
- M4-B：审计日志 + 日配额 + readonly 默认禁用
"""

import logging
import time
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from config import LLM_API_KEY, LLM_ENABLED, LLM_GATEWAY_URL, LLM_MODEL, LLM_TIMEOUT_SEC
from deps_auth import AuthUser
from llm_audit import check_llm_quota, estimate_tokens, log_llm_call, user_may_call_llm

logger = logging.getLogger(__name__)


def llm_enabled() -> bool:
    return LLM_ENABLED and bool(LLM_GATEWAY_URL) and bool(LLM_API_KEY)


async def complete(
    system: str,
    user: str,
    max_tokens: int = 800,
    *,
    db: Optional[Session] = None,
    auth_user: Optional[AuthUser] = None,
    route: str = "unknown",
) -> Optional[str]:
    """返回 LLM 文本；失败或未启用时返回 None（调用方走 fallback）。"""
    t0 = time.perf_counter()

    def _log(status: str, text: Optional[str] = None, msg: Optional[str] = None) -> None:
        if db is None:
            return
        ms = int((time.perf_counter() - t0) * 1000)
        try:
            log_llm_call(
                db,
                user=auth_user,
                route=route,
                status=status,
                latency_ms=ms,
                tokens_est=estimate_tokens(system, user, text),
                message=msg,
            )
        except Exception as exc:
            logger.warning("llm audit log failed: %s", exc)

    if not llm_enabled():
        _log("disabled", msg="LLM 未启用或未配置")
        return None

    if not user_may_call_llm(auth_user):
        _log("disabled", msg="readonly 未开放 LLM")
        return None

    if db is not None:
        quota_msg = check_llm_quota(db, auth_user)
        if quota_msg:
            _log("quota", msg=quota_msg)
            return None

    url = LLM_GATEWAY_URL.rstrip("/")
    if not url.endswith("/chat/completions"):
        url = url + "/v1/chat/completions"
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT_SEC) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"].strip()
            _log("success", text=text)
            return text
    except Exception as exc:
        logger.warning("LLM complete failed: %s", exc)
        _log("error", msg=str(exc)[:200])
        return None
