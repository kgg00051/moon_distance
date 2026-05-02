from __future__ import annotations

import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    from skyfield import almanac
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


@dataclass(frozen=True)
class DistanceExtrema:
    minimum: DailyDistance
    maximum: DailyDistance


def validate_date_components(
    year: int,
    month: int | None,
    sample_hour: int,
    sample_minute: int,
) -> None:
    if year < 1:
        raise ValueError("year must be 1 or greater")
    if month is not None and not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")
    if not 0 <= sample_hour <= 23:
        raise ValueError("sample_hour must be between 0 and 23")
    if not 0 <= sample_minute <= 59:
        raise ValueError("sample_minute must be between 0 and 59")


def build_local_datetimes(
    year: int,
    month: int | None,
    timezone_name: str,
    sample_hour: int = 0,
    sample_minute: int = 0,
) -> list[datetime]:
    validate_date_components(year, month, sample_hour, sample_minute)

    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {timezone_name}") from exc

    target_months = range(1, 13) if month is None else (month,)
    sample_datetimes: list[datetime] = []

    for target_month in target_months:
        _, last_day = calendar.monthrange(year, target_month)
        sample_datetimes.extend(
            datetime(
                year=year,
                month=target_month,
                day=day,
                hour=sample_hour,
                minute=sample_minute,
                tzinfo=timezone,
            )
            for day in range(1, last_day + 1)
        )

    return sample_datetimes


def calculate_daily_moon_distance(
    year: int,
    month: int | None = None,
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


def find_full_moon_distances(
    year: int,
    month: int | None = None,
    *,
    timezone_name: str = "UTC",
    data_dir: Path = DEFAULT_DATA_DIR,
    ephemeris_name: str = DEFAULT_EPHEMERIS,
) -> list[DailyDistance]:
    validate_date_components(year, month, sample_hour=0, sample_minute=0)

    try:
        local_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {timezone_name}") from exc

    period_start_local = datetime(year, month or 1, 1, tzinfo=local_timezone)
    if month is None:
        period_end_local = datetime(year + 1, 1, 1, tzinfo=local_timezone)
    else:
        next_year = year + 1 if month == 12 else year
        next_month = 1 if month == 12 else month + 1
        period_end_local = datetime(next_year, next_month, 1, tzinfo=local_timezone)

    loader = Loader(str(data_dir), verbose=False, expire=False)
    ts = loader.timescale()
    planets = loader(ephemeris_name)

    t0 = ts.from_datetime(period_start_local.astimezone(timezone.utc))
    t1 = ts.from_datetime(period_end_local.astimezone(timezone.utc))
    times, phases = almanac.find_discrete(t0, t1, almanac.moon_phases(planets))

    earth = planets["earth"]
    moon = planets["moon"]
    records: list[DailyDistance] = []

    for time, phase in zip(times, phases):
        if int(phase) != 2:
            continue

        sampled_at_utc = time.utc_datetime()
        if sampled_at_utc.tzinfo is None:
            sampled_at_utc = sampled_at_utc.replace(tzinfo=timezone.utc)
        sampled_at_local = sampled_at_utc.astimezone(local_timezone)

        if not (period_start_local <= sampled_at_local < period_end_local):
            continue

        records.append(
            DailyDistance(
                local_date=sampled_at_local.date(),
                sampled_at=sampled_at_local,
                distance_km=float((moon - earth).at(time).distance().km),
            )
        )

    return records


def extract_plot_data(
    records: Sequence[DailyDistance],
) -> tuple[list[datetime], list[float]]:
    return (
        [record.sampled_at for record in records],
        [record.distance_km for record in records],
    )

