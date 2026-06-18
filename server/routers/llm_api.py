"""M3-B / M4-B LLM 中台状态与审计"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from config import (
    LLM_DAILY_CAP,
    LLM_ENABLED,
    LLM_GATEWAY_URL,
    LLM_MODEL,
    LLM_READONLY_ENABLED,
    LLM_TIMEOUT_SEC,
    LLM_USER_DAILY_CAP,
)
from database import get_db
from deps_auth import AuthUser, get_current_user_optional
from llm_service import llm_enabled
from models import LlmCallLog
from schemas import LlmCallLogOut, LlmStatusOut

router = APIRouter()


@router.get("/api/llm/status", response_model=LlmStatusOut, tags=["LLM"])
def llm_status():
    """模块席联调：看开关、网关是否配置（不含密钥）"""
    return LlmStatusOut(
        enabled=llm_enabled(),
        configured=bool(LLM_GATEWAY_URL and LLM_MODEL),
        llm_enabled_flag=LLM_ENABLED,
        model=LLM_MODEL,
        timeout_sec=LLM_TIMEOUT_SEC,
        gateway_url_set=bool(LLM_GATEWAY_URL),
        daily_cap=LLM_DAILY_CAP,
        user_daily_cap=LLM_USER_DAILY_CAP,
        readonly_llm=LLM_READONLY_ENABLED,
    )


@router.get("/api/llm/audit", response_model=List[LlmCallLogOut], tags=["LLM"])
def llm_audit(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """M4-B：最近 LLM 调用日志（admin）"""
    if not user or not user.is_admin:
        raise HTTPException(403, "需要管理员权限")
    rows = (
        db.query(LlmCallLog)
        .order_by(LlmCallLog.id.desc())
        .limit(limit)
        .all()
    )
    return rows
