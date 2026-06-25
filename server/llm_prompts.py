"""M3-B LLM 提示与规则降级文案（服务端 fallback）"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple


_PLACEHOLDER_MARKERS = (
    "请在 Tab2 手工维护",
    "（待补全竞争格局分析）",
    "（待补全增长机会）",
    "正在生成 AI 解读",
    "请稍候…",
)


def _truncate(text: Optional[str], n: int = 55) -> str:
    if not text:
        return ""
    s = str(text).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def is_strategy_field_empty(val: Optional[str]) -> bool:
    if not val or not str(val).strip():
        return True
    t = str(val).strip()
    if t.startswith("（待补全"):
        return True
    return any(m in t for m in _PLACEHOLDER_MARKERS)


def is_strategy_placeholder_output(text: Optional[str]) -> bool:
    if not text or not str(text).strip():
        return True
    return any(m in str(text) for m in _PLACEHOLDER_MARKERS)


def _build_strategy_rules(
    brand: Any,
    profile: Any,
    metrics: Any,
    alerts: Optional[List[Any]] = None,
) -> Tuple[str, str]:
    """库内无 Tab2 长文时，用经营指标 + 情报拼规则解读（对齐前端 buildStrategyFallback）。"""
    comp_lines: List[str] = []
    opp_lines: List[str] = []
    alerts = alerts or []

    if profile and getattr(profile, "positioning", None):
        comp_lines.append(f"【定位】{_truncate(profile.positioning, 90)}")

    if metrics:
        gmv = getattr(metrics, "gmv", None)
        gmv_yoy = getattr(metrics, "gmv_yoy", None)
        jd_share = getattr(metrics, "jd_share", None)
        jd_share_wow = getattr(metrics, "jd_share_wow", None)
        cg_jd = getattr(metrics, "channel_growth_jd", None)
        cg_dy = getattr(metrics, "channel_growth_douyin", None)

        if jd_share is not None:
            jd_line = f"【渠道】JD 市占 {jd_share}%"
            if jd_share_wow is not None:
                sign = "+" if float(jd_share_wow) > 0 else ""
                jd_line += f"（环比 {sign}{jd_share_wow}pp）"
            comp_lines.append(jd_line)

        if cg_jd is not None and cg_dy is not None and float(cg_dy) > float(cg_jd) + 10:
            comp_lines.append(
                f"【压力】抖音增速 {cg_dy}% 明显高于 JD {cg_jd}%，"
                "需关注站外资源倾斜对 JD 份额的挤压。"
            )
        elif cg_jd is not None and float(cg_jd) < -5:
            comp_lines.append(f"【压力】JD 渠道增速 {cg_jd}%，增长承压，需对齐货盘与价格策略。")

        if gmv_yoy is not None and float(gmv_yoy) < -5:
            comp_lines.append(f"【经营】本期月成交同比 {gmv_yoy}%，需跟踪主要竞对促销与排期。")
        elif gmv is not None and gmv_yoy is not None:
            sign = "+" if float(gmv_yoy) > 0 else ""
            comp_lines.append(f"【经营】本期月成交 {gmv} 万，成交同比 {sign}{gmv_yoy}%。")

    risk_added = False
    for alert in alerts:
        if risk_added:
            break
        if getattr(alert, "priority", None) != "P0":
            continue
        if getattr(alert, "category", None) != "风险预警":
            continue
        title = getattr(alert, "title", None) or _truncate(getattr(alert, "description", None), 40)
        comp_lines.append(f"【情报】{title or 'P0 风险预警'}")
        risk_added = True

    if metrics:
        gmv_yoy = getattr(metrics, "gmv_yoy", None)
        jd_share = getattr(metrics, "jd_share", None)
        cg_dy = getattr(metrics, "channel_growth_douyin", None)
        if gmv_yoy is not None and float(gmv_yoy) > 5:
            opp_lines.append(
                f"【经营】月成交同比 +{gmv_yoy}%，可趁势争取楼层、搜索专区或联合投放资源。"
            )
        if jd_share is not None and float(jd_share) >= 20:
            opp_lines.append(
                f"【品类】JD 市占 {jd_share}% 具备议价基础，可谈 618 专区或新品首发排期。"
            )
        if cg_dy is not None and float(cg_dy) > 15:
            opp_lines.append(f"【渠道】抖音增速 +{cg_dy}%，可推进同价同发或搜索词换资源。")

    opp_added = False
    for alert in alerts:
        if opp_added:
            break
        if getattr(alert, "priority", None) != "P0":
            continue
        if getattr(alert, "category", None) != "增长机会":
            continue
        title = getattr(alert, "title", None) or _truncate(getattr(alert, "description", None), 40)
        opp_lines.append(f"【情报】{title or 'P0 增长机会'}")
        opp_added = True

    level = getattr(brand, "level", "B") if brand else "B"
    name = getattr(brand, "name", "品牌") if brand else "品牌"
    if not comp_lines:
        comp_lines.append(
            f"【解读】{name}（{level}级）结合品类格局与渠道市占，"
            "关注主要竞对在同品类的 JD/抖音动作；可编辑保存为正式竞争分析。"
        )
    if not opp_lines:
        opp_lines.append(
            f"【解读】{name} 结合 GMV 趋势与待办事项，"
            "梳理可争取的楼层、首发与同价同发资源；可编辑保存为正式机会清单。"
        )

    return "\n".join(comp_lines), "\n".join(opp_lines)


def resolve_strategy_baseline(
    landscape: Optional[str],
    opportunities: Optional[str],
    brand: Any,
    profile: Any,
    metrics: Any,
    alerts: Optional[List[Any]] = None,
) -> Tuple[str, str]:
    """优先用库内已保存文案；空库则用规则素材。"""
    built_comp, built_opp = _build_strategy_rules(brand, profile, metrics, alerts)
    comp = landscape if not is_strategy_field_empty(landscape) else built_comp
    opp = opportunities if not is_strategy_field_empty(opportunities) else built_opp
    return comp, opp


def strategy_fallback(landscape: Optional[str], opportunities: Optional[str]) -> Tuple[str, str]:
    """兼容旧调用：仅按字段是否为空返回库内文案或占位（新逻辑请用 resolve_strategy_baseline）。"""
    comp = landscape if not is_strategy_field_empty(landscape) else None
    opp = opportunities if not is_strategy_field_empty(opportunities) else None
    if comp and opp:
        return comp, opp
    built_comp, built_opp = _build_strategy_rules(None, None, None, None)
    return comp or built_comp, opp or built_opp


def build_strategy_llm_context(
    brand: Any,
    profile: Any,
    metrics: Any,
    fb_landscape: str,
    fb_opportunities: str,
) -> str:
    lines = [
        f"品牌：{getattr(brand, 'name', '—')}（{getattr(brand, 'level', 'B')}级）",
        f"负责采销：{getattr(brand, 'responsible', None) or '—'}",
    ]
    if metrics and getattr(metrics, "gmv", None) is not None:
        yoy = getattr(metrics, "gmv_yoy", None)
        yoy_s = f"，成交同比 {yoy}%" if yoy is not None else ""
        lines.append(f"月成交 {metrics.gmv} 万{yoy_s}")
    if profile and getattr(profile, "positioning", None):
        lines.append(f"品牌定位：{profile.positioning}")
    lines.extend(
        [
            "",
            "【竞争格局·规则素材】",
            fb_landscape,
            "",
            "【增长机会·规则素材】",
            fb_opportunities,
            "",
            "请基于以上素材，分别撰写「竞争格局」与「增长机会」两段分析（每段 2-4 条要点，换行分隔）。",
            '输出纯 JSON，不要 markdown 代码块：{"competitive_landscape":"...","growth_opportunities":"..."}',
        ]
    )
    return "\n".join(lines)


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
    result = {
        "competitive_landscape": str(landscape or ""),
        "growth_opportunities": str(opportunities or ""),
    }
    if is_strategy_placeholder_output(result["competitive_landscape"]):
        result["competitive_landscape"] = ""
    if is_strategy_placeholder_output(result["growth_opportunities"]):
        result["growth_opportunities"] = ""
    if not result["competitive_landscape"] and not result["growth_opportunities"]:
        return None
    return result


def blurb_fallback(brand_name: str, metrics: Any, alert_count: int) -> str:
    gmv = getattr(metrics, "gmv", None) if metrics else None
    gmv_yoy = getattr(metrics, "gmv_yoy", None) if metrics else None
    parts = [f"【{brand_name}】"]
    if gmv is not None:
        parts.append(f"月成交约 {gmv} 万")
    if gmv_yoy is not None:
        trend = "回升" if float(gmv_yoy) >= 0 else "承压"
        sign = "+" if float(gmv_yoy) > 0 else ""
        parts.append(f"成交同比 {sign}{gmv_yoy}% {trend}")
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


def briefing_llm_prompt(
    brand_name: str,
    news_titles: list,
    alert_titles: list,
    weekly_text: str,
    gmv_info: str = "",
) -> str:
    news_str = "\n".join(f"- {t}" for t in news_titles[:5]) if news_titles else "（无最新新闻）"
    alert_str = "\n".join(f"- {t}" for t in alert_titles[:5]) if alert_titles else "（无活跃预警）"
    weekly_str = weekly_text or "（无最新周报）"
    prompt = f"""基于以下 {brand_name} 的最新情报，用一段话（≤150字）总结关键发现与建议：

【最新新闻】
{news_str}

【活跃预警】
{alert_str}

【最新周报要点】
{weekly_str}"""
    if gmv_info:
        prompt += f"""

【最新经营数据】
{gmv_info}"""
    prompt += """

请简洁专业：
1. 最值得关注的风险或机会（1-2 条）
2. 建议的下一步动作
3. 如涉及数据，请引用具体数值"""
    return prompt


def feed_llm_prompt(item_title: str, item_body: str, item_type: str) -> str:
    label = "预警" if item_type == "alert" else "新闻"
    return f"""用一句话（≤50字）概括以下{label}的核心要点，保持客观专业：

标题：{item_title}
内容：{item_body or '（无详细内容）'}

直接输出摘要，不要前缀。"""
