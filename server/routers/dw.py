"""M3-C 数仓 v1 · 同步状态 / 批次 / CSV 导入"""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from config import AUTH_REQUIRED
from database import get_db
from deps_auth import AuthUser, get_current_user_optional
from dw_sync import DEFAULT_SAMPLE_CSV, import_csv_file, import_rows
from models import BrandMetrics, DwImportBatch, SyncLog
from schemas import DwBatchOut, DwImportResultOut, DwStatusOut, DwSyncLogOut

router = APIRouter()


def _require_admin(user: Optional[AuthUser]) -> None:
    if not AUTH_REQUIRED:
        return
    if not user:
        raise HTTPException(401, "请先登录")
    if not user.is_admin:
        raise HTTPException(403, "需要管理员权限")


@router.get("/api/dw/status", response_model=DwStatusOut, tags=["数仓"])
def dw_status(db: Session = Depends(get_db)):
    """最近一次同步批次 + 累计统计"""
    last = db.query(DwImportBatch).order_by(DwImportBatch.id.desc()).first()
    metrics_rows = db.query(BrandMetrics).count()
    return DwStatusOut(
        last_batch=DwBatchOut.model_validate(last) if last else None,
        total_batches=db.query(DwImportBatch).count(),
        total_sync_logs=db.query(SyncLog).count(),
        brand_metrics_rows=metrics_rows,
        sample_csv=str(DEFAULT_SAMPLE_CSV.relative_to(Path(__file__).resolve().parent.parent.parent)),
    )


@router.get("/api/dw/batches", response_model=List[DwBatchOut], tags=["数仓"])
def dw_batches(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(DwImportBatch)
        .order_by(DwImportBatch.id.desc())
        .limit(limit)
        .all()
    )
    return rows


@router.get("/api/dw/sync-log", response_model=List[DwSyncLogOut], tags=["数仓"])
def dw_sync_log(
    batch_id: Optional[int] = Query(None),
    name_key: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(SyncLog).order_by(SyncLog.id.desc())
    if batch_id is not None:
        q = q.filter(SyncLog.batch_id == batch_id)
    if name_key:
        q = q.filter(SyncLog.name_key == name_key)
    return q.limit(limit).all()


@router.post("/api/dw/import/csv", response_model=DwImportResultOut, tags=["数仓"])
async def dw_import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """上传 CSV 同步 brand_metrics（AUTH_REQUIRED 时仅 admin）"""
    _require_admin(user)
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "请上传 .csv 文件")
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("gbk", errors="replace")
    import csv
    from io import StringIO

    rows = list(csv.DictReader(StringIO(text)))
    if not rows:
        raise HTTPException(400, "CSV 无数据行")
    batch = import_rows(db, rows, source="csv", source_name=file.filename)
    return DwImportResultOut(batch=batch)


@router.post("/api/dw/sync/sample", response_model=DwImportResultOut, tags=["数仓"])
def dw_sync_sample(
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """导入仓库样例 CSV（本机 smoke / cron 占位）"""
    _require_admin(user)
    if not DEFAULT_SAMPLE_CSV.is_file():
        raise HTTPException(404, f"样例文件不存在: {DEFAULT_SAMPLE_CSV}")
    batch = import_csv_file(db, DEFAULT_SAMPLE_CSV)
    return DwImportResultOut(batch=batch)
