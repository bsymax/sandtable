"""
档案完整度计算（10 分制）
"""

import json
from typing import Optional, List


def _has_text(val: Optional[str]) -> bool:
    return bool(val and str(val).strip())


def calc_completeness(profile, contacts: list, metrics) -> dict:
    score = 0

    if profile:
        if _has_text(profile.positioning):
            score += 1
        if _has_text(profile.founded_year):
            score += 1
        if _has_text(profile.org_structure):
            score += 1
        if _has_text(profile.taboos) and "待补全" not in (profile.taboos or ""):
            score += 1

    if contacts:
        score += 1

    if metrics:
        score += 1
        if metrics.gmv is not None:
            score += 1
        shares = [metrics.jd_share, metrics.tmall_share, metrics.douyin_share, metrics.pdd_share]
        if all(s is not None for s in shares):
            score += 1
        if _has_text(metrics.category_distribution):
            try:
                data = json.loads(metrics.category_distribution)
                if isinstance(data, list) and len(data) > 0:
                    score += 1
            except json.JSONDecodeError:
                pass
        if metrics.gross_margin is not None and metrics.uv_conversion is not None and metrics.ad_rate is not None:
            score += 1

    max_score = 10
    percent = int(round(score / max_score * 100))
    return {
        "completeness_score": score,
        "completeness_max": max_score,
        "completeness_percent": percent,
    }
