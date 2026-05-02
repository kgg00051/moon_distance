from __future__ import annotations

import argparse
import calendar
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    from skyfield.api import Loader
except ModuleNotFoundError as exc:
    raise SystemExit(
        "skyfield is required. Install dependencies with `pip install -r requirements.txt`."
    ) from exc

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_EPHEMERIS = "de421.bsp"


@dataclass(frozen=True)
class DailyDistance:
    local_date: date
    sampled_at: datetime
    distance_km: float


def validate_date_components(
    year: int,
    month: int,
    sample_hour: int,
    sample_minute: int,
) -> None:
    if year < 1:
        raise ValueError("year must be 1 or greater")
    if not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")
    if not 0 <= sample_hour <= 23:
        raise ValueError("sample_hour must be between 0 and 23")
    if not 0 <= sample_minute <= 59:
        raise ValueError("sample_minute must be between 0 and 59")


def build_local_datetimes(
    year: int,
    month: int,
    timezone_name: str,
    sample_hour: int = 0,
    sample_minute: int = 0,
) -> list[datetime]:
    validate_date_components(year, month, sample_hour, sample_minute)

    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {timezone_name}") from exc

    _, last_day = calendar.monthrange(year, month)
    return [
        datetime(
            year=year,
            month=month,
            day=day,
            hour=sample_hour,
            minute=sample_minute,
            tzinfo=timezone,
        )
        for day in range(1, last_day + 1)
    ]


def calculate_daily_moon_distance(
    year: int,
    month: int,
    *,
    timezone_name: str = "UTC",
    sample_hour: int = 0,
    sample_minute: int = 0,
    data_dir: Path = DEFAULT_DATA_DIR,
    ephemeris_name: str = DEFAULT_EPHEMERIS,
) -> list[DailyDistance]:
    sample_datetimes = build_local_datetimes(
        year=year,
        month=month,
        timezone_name=timezone_name,
        sample_hour=sample_hour,
        sample_minute=sample_minute,
    )

    loader = Loader(str(data_dir), verbose=False, expire=False)
    ts = loader.timescale()
    planets = loader(ephemeris_name)

    earth = planets["earth"]
    moon = planets["moon"]

    times = ts.from_datetimes(sample_datetimes)
    distances_km = ((moon - earth).at(times).distance().km).tolist()

    return [
        DailyDistance(
            local_date=sample_datetime.date(),
            sampled_at=sample_datetime,
            distance_km=float(distance_km),
        )
        for sample_datetime, distance_km in zip(sample_datetimes, distances_km)
    ]


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="指定した年月の地球-月距離を1日ごとに計算します。"
    )
    parser.add_argument("year", type=int, help="対象年")
    parser.add_argument("month", type=int, help="対象月")
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

    print("date,sampled_at,distance_km")
    for record in records:
        print(
            f"{record.local_date.isoformat()},"
            f"{record.sampled_at.isoformat()},"
            f"{record.distance_km:.3f}"
        )


if __name__ == "__main__":
    main()
