"""M3-B LLM 中台状态"""

from fastapi import APIRouter

from config import LLM_ENABLED, LLM_GATEWAY_URL, LLM_MODEL, LLM_TIMEOUT_SEC
from llm_service import llm_enabled
from schemas import LlmStatusOut

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
    )
