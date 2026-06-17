"""
M3 LLM 中台（骨架）
- LLM_ENABLED=false 时一律返回 None，由调用方降级 M2 规则版
- M3-B 再接入 DeepSeek / 内网网关
"""

import logging
from typing import Optional

import httpx

from config import LLM_API_KEY, LLM_ENABLED, LLM_GATEWAY_URL, LLM_MODEL, LLM_TIMEOUT_SEC

logger = logging.getLogger(__name__)


def llm_enabled() -> bool:
    return LLM_ENABLED and bool(LLM_GATEWAY_URL) and bool(LLM_API_KEY)


async def complete(system: str, user: str, max_tokens: int = 800) -> Optional[str]:
    """返回 LLM 文本；失败或未启用时返回 None（调用方走 fallback）。"""
    if not llm_enabled():
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
            return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("LLM complete failed: %s", exc)
        return None
