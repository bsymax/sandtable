#!/usr/bin/env python3
"""数仓日更 CLI：CSV → brand_metrics + sync_log

用法:
  cd server && python3 run_dw_sync.py
  cd server && python3 run_dw_sync.py ../data/dw/brand_metrics_weekly.csv
"""

import argparse
import sys
from pathlib import Path

from database import SessionLocal
from dw_sync import DEFAULT_SAMPLE_CSV, import_csv_file


def main() -> int:
    parser = argparse.ArgumentParser(description="数仓 CSV 同步 brand_metrics")
    parser.add_argument(
        "csv",
        nargs="?",
        default=str(DEFAULT_SAMPLE_CSV),
        help="CSV 路径（默认 data/dw/brand_metrics_weekly.csv）",
    )
    args = parser.parse_args()
    path = Path(args.csv)
    if not path.is_file():
        print(f"文件不存在: {path}", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        batch = import_csv_file(db, path)
        print(
            f"batch_key={batch.batch_key} status={batch.status} "
            f"inserted={batch.inserted} updated={batch.updated} "
            f"skipped={batch.skipped} failed={batch.failed}"
        )
        return 0 if batch.status in ("success", "partial") else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
