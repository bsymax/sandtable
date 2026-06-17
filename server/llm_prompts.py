"""M3-B LLM 提示与规则降级文案（服务端 fallback）"""

import json
import re
from typing import Any, Dict, Optional, Tuple


def strategy_fallback(landscape: Optional[str], opportunities: Optional[str]) -> Tuple[str, str]:
    return (
        landscape or "暂无竞争格局描述，请在 Tab2 手工维护。",
        opportunities or "暂无增长机会描述，请在 Tab2 手工维护。",
    )


def parse_strategy_json(raw: str) -> Optional[Dict[str, str]]:
    if not raw:
        return None
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    landscape = data.get("competitive_landscape") or data.get("competitive")
    opportunities = data.get("growth_opportunities") or data.get("opportunities")
    if not landscape and not opportunities:
        return None
    return {
        "competitive_landscape": str(landscape or ""),
        "growth_opportunities": str(opportunities or ""),
    }


def blurb_fallback(brand_name: str, metrics: Any, alert_count: int) -> str:
    gmv = getattr(metrics, "gmv", None) if metrics else None
    wow = getattr(metrics, "gmv_wow", None) if metrics else None
    parts = [f"【{brand_name}】"]
    if gmv is not None:
        parts.append(f"周 GMV 约 {gmv} 万")
    if wow is not None:
        trend = "回升" if float(wow) >= 0 else "承压"
        parts.append(f"环比 {wow}% {trend}")
    if alert_count:
        parts.append(f"待处理情报 {alert_count} 条")
    parts.append("（规则版解读 · LLM 未启用）")
    return "，".join(parts)


def dashboard_summary_fallback(
    todo_pending: int,
    todo_overdue: int,
    commit_pending: int,
    p0p1: int,
    health_warn: int,
) -> str:
    parts = ["今日工作台"]
    if todo_overdue:
        parts.append(f"{todo_overdue} 项待办已逾期")
    elif todo_pending:
        parts.append(f"{todo_pending} 项待办待处理")
    if commit_pending:
        parts.append(f"{commit_pending} 条承诺待跟进")
    if p0p1:
        parts.append(f"{p0p1} 条 P0/P1 情报")
    if health_warn:
        parts.append(f"{health_warn} 个品牌拜访频率偏低")
    if len(parts) == 1:
        parts.append("暂无紧急事项，可按计划拜访")
    parts.append("（规则版 · LLM 未启用）")
    return " · ".join(parts)
