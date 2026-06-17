"""M3-C 数仓 v1 · CSV/API 行导入 brand_metrics + 同步日志"""

from __future__ import annotations

import csv
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models import Brand, BrandMetrics, DwImportBatch, SyncLog

METRIC_FIELDS = [
    "gmv", "gmv_wow", "gmv_yoy", "sales_volume", "sales_volume_wow",
    "jd_share", "jd_share_wow", "tmall_share", "douyin_share", "pdd_share",
    "channel_growth_jd", "channel_growth_tmall", "channel_growth_douyin",
    "category_distribution", "category_share",
    "sku_count", "p0_gap_count", "gross_margin", "uv_conversion", "ad_rate",
]

INT_FIELDS = {"sales_volume", "sku_count", "p0_gap_count"}
TEXT_FIELDS = {"category_distribution", "category_share"}

DEFAULT_SAMPLE_CSV = (
    Path(__file__).resolve().parent.parent / "data" / "dw" / "brand_metrics_weekly.csv"
)


def _parse_value(field: str, raw: Any) -> Any:
    if raw is None or str(raw).strip() == "":
        return None
    s = str(raw).strip()
    if field in TEXT_FIELDS:
        return s
    if field in INT_FIELDS:
        return int(float(s))
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} 格式错误: {raw}") from exc


def normalize_row(raw: Dict[str, Any]) -> Dict[str, Any]:
    row = {k.strip().lower(): v for k, v in raw.items() if k and str(k).strip()}
    name_key = (row.get("name_key") or "").strip()
    period_value = (row.get("period_value") or "").strip()
    period_type = (row.get("period_type") or "weekly").strip().lower()
    if period_type not in ("weekly", "monthly"):
        period_type = "weekly"
    out: Dict[str, Any] = {
        "name_key": name_key,
        "period_type": period_type,
        "period_value": period_value,
    }
    for field in METRIC_FIELDS:
        if field in row:
            out[field] = _parse_value(field, row[field])
    return out


def _append_log(
    db: Session,
    batch_id: int,
    *,
    brand_id: Optional[int] = None,
    name_key: Optional[str] = None,
    period_value: Optional[str] = None,
    action: str,
    message: Optional[str] = None,
) -> None:
    db.add(
        SyncLog(
            batch_id=batch_id,
            brand_id=brand_id,
            name_key=name_key,
            period_value=period_value,
            action=action,
            message=(message or "")[:512] or None,
        )
    )


def import_rows(
    db: Session,
    rows: List[Dict[str, Any]],
    *,
    source: str = "csv",
    source_name: Optional[str] = None,
) -> DwImportBatch:
    batch = DwImportBatch(
        batch_key=str(uuid.uuid4()),
        source=source,
        source_name=source_name,
        status="running",
        total_rows=len(rows),
    )
    db.add(batch)
    db.flush()

    brands = {b.name_key: b for b in db.query(Brand).all()}
    inserted = updated = skipped = failed = 0
    errors: List[str] = []

    for idx, raw in enumerate(rows, start=1):
        try:
            row = normalize_row(raw)
            name_key = row["name_key"]
            period_value = row["period_value"]
            if not name_key or not period_value:
                skipped += 1
                _append_log(
                    db, batch.id,
                    name_key=name_key or None,
                    period_value=period_value or None,
                    action="skip",
                    message="缺少 name_key 或 period_value",
                )
                continue

            brand = brands.get(name_key)
            if not brand:
                failed += 1
                msg = f"未知品牌 name_key={name_key}"
                errors.append(msg)
                _append_log(
                    db, batch.id,
                    name_key=name_key,
                    period_value=period_value,
                    action="error",
                    message=msg,
                )
                continue

            existing = (
                db.query(BrandMetrics)
                .filter(
                    BrandMetrics.brand_id == brand.id,
                    BrandMetrics.period_type == row["period_type"],
                    BrandMetrics.period_value == period_value,
                )
                .first()
            )

            payload = {f: row[f] for f in METRIC_FIELDS if f in row and row[f] is not None}

            if existing:
                changed = False
                for field, value in payload.items():
                    if getattr(existing, field) != value:
                        setattr(existing, field, value)
                        changed = True
                if changed:
                    updated += 1
                    _append_log(
                        db, batch.id,
                        brand_id=brand.id,
                        name_key=name_key,
                        period_value=period_value,
                        action="update",
                        message="指标已更新",
                    )
                else:
                    skipped += 1
                    _append_log(
                        db, batch.id,
                        brand_id=brand.id,
                        name_key=name_key,
                        period_value=period_value,
                        action="skip",
                        message="无变化",
                    )
            else:
                db.add(
                    BrandMetrics(
                        brand_id=brand.id,
                        period_type=row["period_type"],
                        period_value=period_value,
                        **payload,
                    )
                )
                inserted += 1
                _append_log(
                    db, batch.id,
                    brand_id=brand.id,
                    name_key=name_key,
                    period_value=period_value,
                    action="insert",
                    message="新增周期",
                )
        except Exception as exc:
            failed += 1
            msg = f"行{idx}: {exc}"
            errors.append(msg)
            _append_log(db, batch.id, action="error", message=msg)

    batch.inserted = inserted
    batch.updated = updated
    batch.skipped = skipped
    batch.failed = failed
    batch.finished_at = datetime.utcnow()
    if failed and (inserted or updated):
        batch.status = "partial"
    elif failed:
        batch.status = "failed"
    else:
        batch.status = "success"
    if errors:
        batch.error_summary = "; ".join(errors[:5])

    db.commit()
    db.refresh(batch)
    return batch


def import_csv_file(
    db: Session,
    path: Path,
    *,
    source_name: Optional[str] = None,
) -> DwImportBatch:
    path = Path(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return import_rows(db, rows, source="csv", source_name=source_name or path.name)
