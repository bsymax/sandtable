"""M4-B · LLM 审计与配额"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from config import LLM_DAILY_CAP, LLM_READONLY_ENABLED, LLM_USER_DAILY_CAP
from deps_auth import AuthUser
from models import LlmCallLog


def user_may_call_llm(user: Optional[AuthUser]) -> bool:
    if user and user.role == "readonly" and not LLM_READONLY_ENABLED:
        return False
    return True


def _today_start() -> datetime:
    now = datetime.utcnow()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def check_llm_quota(db: Session, user: Optional[AuthUser]) -> Optional[str]:
    """超限返回原因文案；未超限返回 None"""
    if LLM_DAILY_CAP > 0:
        site_n = (
            db.query(LlmCallLog)
            .filter(LlmCallLog.created_at >= _today_start())
            .filter(LlmCallLog.status.in_(("success", "fallback")))
            .count()
        )
        if site_n >= LLM_DAILY_CAP:
            return f"全站日配额已满（{LLM_DAILY_CAP}）"
    if user and LLM_USER_DAILY_CAP > 0:
        user_n = (
            db.query(LlmCallLog)
            .filter(LlmCallLog.user_id == user.id, LlmCallLog.created_at >= _today_start())
            .filter(LlmCallLog.status.in_(("success", "fallback")))
            .count()
        )
        if user_n >= LLM_USER_DAILY_CAP:
            return f"用户日配额已满（{LLM_USER_DAILY_CAP}）"
    return None


def log_llm_call(
    db: Session,
    *,
    user: Optional[AuthUser],
    route: str,
    status: str,
    latency_ms: Optional[int] = None,
    tokens_est: Optional[int] = None,
    message: Optional[str] = None,
) -> None:
    row = LlmCallLog(
        user_id=user.id if user else None,
        username=user.username if user else None,
        route=route[:128],
        status=status,
        latency_ms=latency_ms,
        tokens_est=tokens_est,
        message=(message or "")[:512] or None,
    )
    db.add(row)
    db.commit()


def estimate_tokens(system: str, user: str, response: Optional[str]) -> int:
    total = len(system) + len(user) + (len(response) if response else 0)
    return max(1, total // 4)
