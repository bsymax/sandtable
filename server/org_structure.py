"""
组织架构 JSON · 解析 / 与关键人物同步

结构：
{
  "root": "集团",
  "lead": "事业部",
  "branches": [{"id": "b1", "label": "京东渠道组"}],
  "nodes": [{"id": "n1", "label": "张三 · 总监", "contact_id": 12, "branch_id": "b1"}],
  "image_url": "/uploads/org/nippon/xxx.png",
  "image_updated_at": "2026-07-01"
}
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional


def new_org_id(prefix: str = "n") -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def contact_org_label(name: str, title: Optional[str]) -> str:
    title = (title or "").strip()
    if not title:
        return name
    roles = ["总经理", "副总经理", "总监", "副总监", "经理", "主管", "负责人", "VP"]
    for suffix in roles:
        if suffix in title:
            return f"{name} · {suffix}"
    if len(title) <= 6:
        return f"{name} · {title}"
    return f"{name} · {title[-4:]}"


def parse_org_structure(raw: Any) -> dict:
    default = {"root": "", "lead": "", "branches": [], "nodes": []}
    if not raw:
        return default.copy()
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return default.copy()
    if not isinstance(data, dict):
        return default.copy()

    branches = []
    for item in data.get("branches") or []:
        if isinstance(item, str):
            label = item.strip()
            if label:
                branches.append({"id": new_org_id("b"), "label": label})
        elif isinstance(item, dict):
            label = (item.get("label") or "").strip()
            if label:
                branches.append(
                    {
                        "id": item.get("id") or new_org_id("b"),
                        "label": label,
                    }
                )

    nodes = []
    for item in data.get("nodes") or []:
        if isinstance(item, str):
            label = item.strip()
            if label:
                nodes.append(
                    {
                        "id": new_org_id("n"),
                        "label": label,
                        "contact_id": None,
                        "branch_id": None,
                    }
                )
        elif isinstance(item, dict):
            label = (item.get("label") or "").strip()
            if not label:
                continue
            branch_id = item.get("branch_id")
            nodes.append(
                {
                    "id": item.get("id") or new_org_id("n"),
                    "label": label,
                    "contact_id": item.get("contact_id"),
                    "branch_id": branch_id if branch_id else None,
                }
            )

    result = {
        "root": (data.get("root") or "").strip(),
        "lead": (data.get("lead") or "").strip(),
        "branches": branches,
        "nodes": nodes,
    }
    image_url = (data.get("image_url") or "").strip()
    if image_url:
        result["image_url"] = image_url
    if data.get("image_updated_at"):
        result["image_updated_at"] = str(data.get("image_updated_at"))
    return result


def dump_org_structure(org: dict) -> str:
    return json.dumps(org, ensure_ascii=False)


def guess_branch_id(contact, branches: list[dict]) -> Optional[str]:
    title = (contact.title or "").strip()
    role = (getattr(contact, "role_tag", None) or "").strip()
    haystack = f"{title} {role}"
    if not haystack.strip():
        return None

    for branch in branches:
        label = (branch.get("label") or "").strip()
        if not label:
            continue
        if label in title or label in role or label in haystack:
            return branch["id"]

    keywords = [
        "京东", "JD", "天猫", "淘宝", "抖音", "内容电商",
        "电商", "市场", "品牌", "财务", "结算", "供应链", "履约",
    ]
    for branch in branches:
        blabel = branch.get("label") or ""
        for kw in keywords:
            if kw in blabel and kw in haystack:
                return branch["id"]
    return None


def sync_org_from_contacts(profile, contacts) -> None:
    """关键人物变更后：更新/追加节点；职务与分支匹配则归入分支，否则默认下层。"""
    org = parse_org_structure(profile.org_structure)
    image_url = org.get("image_url")
    image_updated_at = org.get("image_updated_at")
    branches = org["branches"]
    nodes = org["nodes"]
    active_ids = {c.id for c in contacts if c.is_active}

    nodes = [
        n
        for n in nodes
        if not n.get("contact_id") or n["contact_id"] in active_ids
    ]
    by_contact = {n["contact_id"]: n for n in nodes if n.get("contact_id")}

    for contact in contacts:
        if not contact.is_active:
            continue
        label = contact_org_label(contact.name, contact.title)
        branch_id = guess_branch_id(contact, branches)

        if contact.id in by_contact:
            node = by_contact[contact.id]
            node["label"] = label
            if branch_id is not None:
                node["branch_id"] = branch_id
            continue

        matched_manual = None
        for node in nodes:
            if node.get("contact_id"):
                continue
            node_label = node.get("label") or ""
            if contact.name in node_label or node_label in label:
                node["contact_id"] = contact.id
                node["label"] = label
                if branch_id is not None:
                    node["branch_id"] = branch_id
                matched_manual = node
                break

        if not matched_manual:
            nodes.append(
                {
                    "id": new_org_id("n"),
                    "label": label,
                    "contact_id": contact.id,
                    "branch_id": branch_id,
                }
            )

    org["nodes"] = nodes
    if image_url:
        org["image_url"] = image_url
    if image_updated_at:
        org["image_updated_at"] = image_updated_at
    profile.org_structure = dump_org_structure(org)


def apply_org_update(profile, payload: dict) -> None:
    org = parse_org_structure(profile.org_structure)
    if payload.get("clear_image"):
        org.pop("image_url", None)
        org.pop("image_updated_at", None)
    if payload.get("root") is not None:
        org["root"] = (payload["root"] or "").strip()
    if payload.get("lead") is not None:
        org["lead"] = (payload["lead"] or "").strip()
    if payload.get("branches") is not None:
        org["branches"] = parse_org_structure({"branches": payload["branches"]})["branches"]
    if payload.get("nodes") is not None:
        org["nodes"] = parse_org_structure({"nodes": payload["nodes"]})["nodes"]
    profile.org_structure = dump_org_structure(org)
