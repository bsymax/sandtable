"""M3-B / M4-B LLM 中台状态与审计 · M5 admin 诊断"""

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
from deps_auth import AuthUser, get_admin_user, get_current_user_optional
from llm_diagnostics import (
    build_config_snapshot,
    diagnose_runtime,
    last_error_message,
    probe_gateway,
    recent_logs,
    route_stats_today,
    today_stats,
)
from llm_service import llm_enabled
from models import LlmCallLog
from schemas import (
    LlmAdminOverviewOut,
    LlmCallLogOut,
    LlmConfigSnapshotOut,
    LlmProbeOut,
    LlmRouteStatOut,
    LlmStatusOut,
    LlmTodayStatsOut,
)

router = APIRouter()


def _status_out() -> LlmStatusOut:
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


@router.get("/api/llm/status", response_model=LlmStatusOut, tags=["LLM"])
def llm_status():
    """模块席联调：看开关、网关是否配置（不含密钥）"""
    return _status_out()


@router.get("/api/llm/admin/overview", response_model=LlmAdminOverviewOut, tags=["LLM"])
def llm_admin_overview(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_admin_user),
):
    """admin：配置快照 + 今日统计 + 排查提示"""
    _ = user
    cfg = build_config_snapshot()
    stats = today_stats(db)
    return LlmAdminOverviewOut(
        status=_status_out(),
        config=LlmConfigSnapshotOut(**cfg),
        today=LlmTodayStatsOut(**stats),
        route_stats=[LlmRouteStatOut(**row) for row in route_stats_today(db)],
        last_error=last_error_message(db),
        tips=diagnose_runtime(db),
    )


@router.post("/api/llm/admin/probe", response_model=LlmProbeOut, tags=["LLM"])
async def llm_admin_probe(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_admin_user),
):
    """admin：对网关发最小 completions 探活（不计入业务配额）"""
    result = await probe_gateway(db=db, auth_user=user)
    return LlmProbeOut(**result)


@router.get("/api/llm/audit", response_model=List[LlmCallLogOut], tags=["LLM"])
def llm_audit(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """M4-B：最近 LLM 调用日志（admin）"""
    if not user or not user.is_admin:
        raise HTTPException(403, "需要管理员权限")
    return recent_logs(db, limit=limit)
