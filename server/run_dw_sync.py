#!/usr/bin/env python3
"""数仓同步 CLI：CSV → brand_metrics + sync_log

用法:
  cd server && python3 run_dw_sync.py
  cd server && python3 run_dw_sync.py ../data/dw/bi_export.csv --bi
  cd server && python3 run_dw_sync.py ../data/dw/brand_metrics_monthly.csv --bi
  cd server && python3 run_dw_sync.py --retry-batch <batch_key>
"""

import argparse
import sys
from pathlib import Path

from database import SessionLocal
from dw_sync import DEFAULT_SAMPLE_CSV, import_csv_file, retry_batch


def main() -> int:
    parser = argparse.ArgumentParser(description="数仓 CSV 同步 brand_metrics")
    parser.add_argument(
        "csv",
        nargs="?",
        default=None,
        help="CSV 路径（默认 data/dw/brand_metrics_weekly.csv）",
    )
    parser.add_argument(
        "--bi",
        action="store_true",
        help="按 BI 映射解析 brand_id → name_key，批次标记 bi_csv",
    )
    parser.add_argument(
        "--retry-batch",
        metavar="BATCH_KEY",
        help="按批次 source_name 重跑同一 CSV 文件",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.retry_batch:
            batch = retry_batch(db, args.retry_batch)
        else:
            path = Path(args.csv) if args.csv else DEFAULT_SAMPLE_CSV
            if not path.is_file():
                print(f"文件不存在: {path}", file=sys.stderr)
                return 1
            batch = import_csv_file(db, path, apply_bi=args.bi)

        print(
            f"batch_key={batch.batch_key} source={batch.source} status={batch.status} "
            f"inserted={batch.inserted} updated={batch.updated} "
            f"skipped={batch.skipped} failed={batch.failed}"
        )
        return 0 if batch.status in ("success", "partial") else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
