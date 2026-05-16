"""
批量历史回填：对每个目标日期调用 main.py
用法：python scripts/batch_backfill.py --from 2026-04-21 --to 2026-05-15
"""
import sys
import os
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))


def daterange(start_str, end_str):
    start = datetime.strptime(start_str, "%Y-%m-%d")
    end = datetime.strptime(end_str, "%Y-%m-%d")
    d = start
    while d <= end:
        yield d.strftime("%Y-%m-%d")
        d += timedelta(days=1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="date_from", default="2026-04-21")
    parser.add_argument("--to", dest="date_to", default="2026-05-15")
    args = parser.parse_args()

    dates = list(daterange(args.date_from, args.date_to))
    print(f"批量回填：{args.date_from} ~ {args.date_to}，共 {len(dates)} 天")
    print()

    from main import main, cleanup_old_data

    success, skipped, failed = 0, 0, 0
    for i, date_str in enumerate(dates, 1):
        print(f"\n{'='*50}")
        print(f"[{i}/{len(dates)}] {date_str}")
        print(f"{'='*50}")
        try:
            main(date_str)
            success += 1
        except Exception as e:
            print(f"[ERROR] {date_str}: {e}")
            failed += 1

    cleanup_old_data()
    print(f"\n\n批量完成：成功 {success} / 跳过 {skipped} / 失败 {failed}")
