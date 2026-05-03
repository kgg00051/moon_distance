from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from moon_distance import (
    DEFAULT_DATA_DIR,
    DEFAULT_EPHEMERIS,
    DailyDistance,
    calculate_daily_moon_distance,
    extract_plot_data,
    find_full_moon_distances,
)

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_MPLCONFIG_DIR = Path(__file__).resolve().parent / ".mplconfig"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent / ".cache"


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
    parser.add_argument(
        "--plot-output",
        type=Path,
        default=None,
        help="グラフ画像の保存先。既定では output/ 配下に PNG を保存",
    )
    parser.add_argument(
        "--show-plot",
        action="store_true",
        help="保存したグラフを画面表示する",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="matplotlib によるグラフ出力を行わない",
    )
    parser.add_argument(
        "--no-full-moon",
        action="store_true",
        help="グラフ上の満月マーカーと注釈を表示しない",
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


def build_default_plot_path(year: int, month: int | None) -> Path:
    suffix = str(year) if month is None else f"{year}_{month:02d}"
    return DEFAULT_OUTPUT_DIR / f"moon_distance_{suffix}.png"


def build_plot_title(year: int, month: int | None) -> str:
    period = str(year) if month is None else f"{year}-{month:02d}"
    return f"Moon-Earth Distance ({period})"


def build_extrema_label(label: str, record: DailyDistance) -> str:
    return (
        f"{label}\n"
        f"{record.local_date.isoformat()}\n"
        f"{record.distance_km:,.0f} km"
    )


def build_annotation_position(
    records: list[DailyDistance],
    record: DailyDistance,
    *,
    place_above: bool,
) -> tuple[tuple[int, int], str, str]:
    midpoint = records[0].sampled_at + (records[-1].sampled_at - records[0].sampled_at) / 2
    #x_offset = -12 if record.sampled_at >= midpoint else 12
    x_offset = 12
    #y_offset = 12 if place_above else -32
    y_offset = 12 if place_above else -40
    horizontal_alignment = "right" if x_offset < 0 else "left"
    vertical_alignment = "bottom" if y_offset > 0 else "top"
    return (x_offset, y_offset), horizontal_alignment, vertical_alignment


def configure_matplotlib() -> None:
    if "XDG_CACHE_HOME" not in os.environ:
        DEFAULT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        os.environ["XDG_CACHE_HOME"] = str(DEFAULT_CACHE_DIR)
    if "MPLCONFIGDIR" not in os.environ:
        DEFAULT_MPLCONFIG_DIR.mkdir(parents=True, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = str(DEFAULT_MPLCONFIG_DIR)


def plot_records(
    records: list[DailyDistance],
    *,
    year: int,
    month: int | None,
    output_path: Path,
    show_plot: bool,
    full_moon_records: list[DailyDistance] | None = None,
) -> Path:
    configure_matplotlib()

    import matplotlib

    if not show_plot:
        matplotlib.use("Agg")

    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    sampled_at, distance_km = extract_plot_data(records)
    resolved_output_path = output_path.expanduser()
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sampled_at, distance_km, color="#1f5aa6", linewidth=2.0)
    ax.fill_between(sampled_at, distance_km, color="#8bb8e8", alpha=0.25)
    ax.set_title(build_plot_title(year, month), y=-0.2)
    ax.set_xlabel("Date")
    ax.set_ylabel("Distance (km)")
    ax.set_ylim(0, 500000)
    ax.grid(True, color="#d7dce2", linewidth=0.8)

    if full_moon_records:
        full_moon_sampled_at, full_moon_distance_km = extract_plot_data(full_moon_records)
        ax.scatter(
            full_moon_sampled_at,
            full_moon_distance_km,
            color="#5f3dc4",
            edgecolors="white",
            linewidths=0.8,
            marker="*",
            s=160,
            zorder=4,
            label="Full Moon",
        )
        for index, record in enumerate(full_moon_records):
            offset, horizontal_alignment, vertical_alignment = build_annotation_position(
                records,
                record,
                place_above=(index % 2 == 0),
            )
            ax.annotate(
                build_extrema_label("Full Moon", record),
                xy=(record.sampled_at, record.distance_km),
                xytext=offset,
                textcoords="offset points",
                ha=horizontal_alignment,
                va=vertical_alignment,
                color="#5f3dc4",
                fontsize=9,
                bbox={"boxstyle": "round,pad=0.3", "fc": "#f3f0ff", "ec": "#7950f2"},
                arrowprops={"arrowstyle": "->", "color": "#7950f2", "lw": 1.0},
            )

    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.legend(loc="lower right")

    fig.tight_layout()
    fig.savefig(resolved_output_path, dpi=150)

    if show_plot:
        plt.show()

    plt.close(fig)
    return resolved_output_path.resolve()


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.no_plot and args.plot_output is not None:
        parser.error("--no-plot cannot be used with --plot-output")
    if args.no_plot and args.show_plot:
        parser.error("--no-plot cannot be used with --show-plot")

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

    full_moon_records: list[DailyDistance] = []
    if not args.no_plot and not args.no_full_moon:
        try:
            full_moon_records = find_full_moon_distances(
                args.year,
                args.month,
                timezone_name=args.timezone,
                data_dir=args.data_dir,
                ephemeris_name=args.ephemeris,
            )
        except ValueError as exc:
            parser.error(str(exc))

    print_csv(records)

    if not args.no_plot:
        output_path = args.plot_output or build_default_plot_path(args.year, args.month)
        saved_path = plot_records(
            records,
            year=args.year,
            month=args.month,
            output_path=output_path,
            show_plot=args.show_plot,
            full_moon_records=full_moon_records,
        )
        print(f"Plot saved to {saved_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
