"""
档案完整度计算（12 分制）

1-4  定位 / 成立时间 / 组织架构 / 潜规则（非「待补全」）
5    有关键人物
6-10 经营指标（快照、GMV、四渠道市占、类目分布、深度指标）
11   有品牌情报（intel_alerts + intel_news，不限 P0/P1，含全部优先级与状态）
12   有互动记录（visits，含已安排/已完成等）
"""

import json
from typing import Optional, Set

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

_table_cache: Optional[Set[str]] = None


def _has_text(val: Optional[str]) -> bool:
    return bool(val and str(val).strip())


def _existing_tables(engine) -> Set[str]:
    global _table_cache
    if _table_cache is None:
        _table_cache = set(inspect(engine).get_table_names())
    return _table_cache


def count_brand_intel(db: Session, engine, brand_id: int) -> int:
    """统计品牌全部情报条数（预警 + 新闻，不限优先级）。"""
    tables = _existing_tables(engine)
    total = 0
    if "intel_alerts" in tables:
        total += (
            db.execute(
                text("SELECT COUNT(*) FROM intel_alerts WHERE brand_id = :bid"),
                {"bid": brand_id},
            ).scalar()
            or 0
        )
    if "intel_news" in tables:
        total += (
            db.execute(
                text("SELECT COUNT(*) FROM intel_news WHERE brand_id = :bid"),
                {"bid": brand_id},
            ).scalar()
            or 0
        )
    return total


def count_brand_interactions(db: Session, engine, brand_id: int) -> int:
    """统计品牌拜访/互动安排条数。"""
    tables = _existing_tables(engine)
    if "visits" not in tables:
        return 0
    return (
        db.execute(
            text("SELECT COUNT(*) FROM visits WHERE brand_id = :bid"),
            {"bid": brand_id},
        ).scalar()
        or 0
    )


def calc_completeness(
    profile,
    contacts: list,
    metrics,
    *,
    intel_count: int = 0,
    interaction_count: int = 0,
) -> dict:
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

    if intel_count > 0:
        score += 1
    if interaction_count > 0:
        score += 1

    max_score = 12
    percent = int(round(score / max_score * 100))
    return {
        "completeness_score": score,
        "completeness_max": max_score,
        "completeness_percent": percent,
    }
