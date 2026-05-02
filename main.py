from __future__ import annotations

import argparse
from pathlib import Path

from moon_distance import (
    DEFAULT_DATA_DIR,
    DEFAULT_EPHEMERIS,
    DailyDistance,
    calculate_daily_moon_distance,
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="指定した年、または年月の地球-月距離を1日ごとに計算します。"
    )
    parser.add_argument("year", type=int, help="対象年")
    parser.add_argument(
        "month",
        type=int,
        nargs="?",
        default=None,
        help="対象月。省略時は1年分を計算",
    )
    parser.add_argument(
        "--timezone",
        default="UTC",
        help="日付の基準にするタイムゾーン名。例: UTC, Asia/Tokyo",
    )
    parser.add_argument(
        "--hour",
        type=int,
        default=0,
        help="各日で距離を評価する時刻の時。既定値は 0",
    )
    parser.add_argument(
        "--minute",
        type=int,
        default=0,
        help="各日で距離を評価する時刻の分。既定値は 0",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"エフェメリス保存先。既定値は {DEFAULT_DATA_DIR}",
    )
    parser.add_argument(
        "--ephemeris",
        default=DEFAULT_EPHEMERIS,
        help=f"使用する JPL エフェメリス。既定値は {DEFAULT_EPHEMERIS}",
    )
    return parser


def print_csv(records: list[DailyDistance]) -> None:
    print("date,sampled_at,distance_km")
    for record in records:
        print(
            f"{record.local_date.isoformat()},"
            f"{record.sampled_at.isoformat()},"
            f"{record.distance_km:.3f}"
        )


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    try:
        records = calculate_daily_moon_distance(
            args.year,
            args.month,
            timezone_name=args.timezone,
            sample_hour=args.hour,
            sample_minute=args.minute,
            data_dir=args.data_dir,
            ephemeris_name=args.ephemeris,
        )
    except ValueError as exc:
        parser.error(str(exc))

    print_csv(records)


if __name__ == "__main__":
    main()
