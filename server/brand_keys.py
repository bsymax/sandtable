"""品牌 name_key 解析 · CSV legacy 别名 → 库内五品牌"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
MASTER_PATH = ROOT / "data" / "brands_master.json"


@lru_cache(maxsize=1)
def load_legacy_name_key_map() -> Dict[str, str]:
    if not MASTER_PATH.is_file():
        return {}
    data = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    raw = data.get("legacy_name_key_map") or {}
    return {str(k).strip().lower(): str(v).strip() for k, v in raw.items() if k and v}


def resolve_brand_key(raw_key: str, active_keys: Set[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    返回 (canonical_key, legacy_source)。
    canonical 在 active_keys 内则成功；legacy_source 非空表示经 legacy 映射。
    """
    key = (raw_key or "").strip().lower()
    if not key:
        return None, None
    if key in active_keys:
        return key, None
    legacy = load_legacy_name_key_map()
    mapped = legacy.get(key)
    if mapped and mapped in active_keys:
        return mapped, key
    return None, key if key in legacy else None


def resolve_brand_keys(raw_keys: Iterable[str], active_keys: Set[str]) -> Tuple[List[str], List[str]]:
    """去重后的 canonical keys；unknown 为无法解析的原始 key。"""
    canonical: List[str] = []
    unknown: List[str] = []
    seen: Set[str] = set()
    for raw in raw_keys:
        key = (raw or "").strip()
        if not key:
            continue
        resolved, _legacy = resolve_brand_key(key, active_keys)
        if resolved:
            if resolved not in seen:
                seen.add(resolved)
                canonical.append(resolved)
        else:
            unknown.append(key)
    return canonical, unknown
