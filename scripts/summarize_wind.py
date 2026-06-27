from pathlib import Path
import sys

import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_wind_file
from src.wind import (
    ANEMOMETER_HEIGHT_M,
    REFERENCE_HEIGHT_M,
    WIND_PROFILE_EXPONENT,
    height_correction_factor,
    mps_to_mph,
)

# Gust averaging window. Wind unit conversion and the reference-height
# correction live in ``src.wind`` and are applied in ``read_wind_file``.
GUST_AVERAGING_SECONDS = 3.0

WIND_FILES = [
    Path("data/2023-03-01/Wind Sensor/08N4S-20230301_005350.txt"),
    Path("data/2025-12-27/Wind Sensor/31S4S-20251227_000722.txt"),
    # Update these filenames to match your actual files.
]

OUT_DIR = Path("results/wind")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def summarize_file(file_path, window="30min"):
    print(f"Reading {file_path}")

    meta, df = read_wind_file(file_path)

    # Original sampling rate from metadata drives the 3-second gust window.
    fs = float(meta["sampling_rate_hz"])
    gust_window_samples = max(1, int(round(GUST_AVERAGING_SECONDS * fs)))

    df = df.set_index("timestamp")

    # Rolling 3-second average wind speed, computed for both the raw
    # (roof-level) signal and the reference-height-corrected signal.
    df["wind_3s_avg_roof_m_s"] = (
        df["wind_m_s"].rolling(window=gust_window_samples, min_periods=1).mean()
    )
    df["wind_3s_avg_10m_m_s"] = (
        df["wind_ref_m_s"].rolling(window=gust_window_samples, min_periods=1).mean()
    )

    grouped = df.resample(window)

    summary = grouped["wind_m_s"].agg(
        wind_mean_roof_m_s="mean",
        wind_median_roof_m_s="median",
        wind_max_raw_roof_m_s="max",
        wind_std_roof_m_s="std",
        n_samples="count",
    )

    # Reference-height-corrected statistics, aggregated from wind_ref_m_s.
    ref = grouped["wind_ref_m_s"].agg(
        wind_mean_10m_m_s="mean",
        wind_median_10m_m_s="median",
        wind_max_raw_10m_m_s="max",
        wind_std_10m_m_s="std",
    )
    summary = summary.join(ref)

    # 3-second gust is the peak rolling 3-second average within each window.
    summary["wind_3s_gust_roof_m_s"] = grouped["wind_3s_avg_roof_m_s"].max()
    summary["wind_3s_gust_10m_m_s"] = grouped["wind_3s_avg_10m_m_s"].max()

    summary = summary.reset_index()

    summary["dataset"] = meta["Start_date"]
    summary["channel"] = meta["channel"]
    summary["window"] = window
    summary["anemometer_height_m"] = ANEMOMETER_HEIGHT_M
    summary["reference_height_m"] = REFERENCE_HEIGHT_M
    summary["wind_profile_exponent"] = WIND_PROFILE_EXPONENT

    # Convenient mph columns for both roof and 10 m corrected speeds.
    summary["wind_mean_roof_mph"] = mps_to_mph(summary["wind_mean_roof_m_s"])
    summary["wind_3s_gust_roof_mph"] = mps_to_mph(summary["wind_3s_gust_roof_m_s"])
    summary["wind_max_raw_roof_mph"] = mps_to_mph(summary["wind_max_raw_roof_m_s"])
    summary["wind_mean_10m_mph"] = mps_to_mph(summary["wind_mean_10m_m_s"])
    summary["wind_3s_gust_10m_mph"] = mps_to_mph(summary["wind_3s_gust_10m_m_s"])
    summary["wind_max_raw_10m_mph"] = mps_to_mph(summary["wind_max_raw_10m_m_s"])

    column_order = [
        "timestamp",
        "dataset",
        "channel",
        "window",
        "anemometer_height_m",
        "reference_height_m",
        "wind_profile_exponent",
        "wind_mean_roof_m_s",
        "wind_median_roof_m_s",
        "wind_max_raw_roof_m_s",
        "wind_std_roof_m_s",
        "wind_3s_gust_roof_m_s",
        "wind_mean_10m_m_s",
        "wind_median_10m_m_s",
        "wind_max_raw_10m_m_s",
        "wind_std_10m_m_s",
        "wind_3s_gust_10m_m_s",
        "wind_mean_roof_mph",
        "wind_3s_gust_roof_mph",
        "wind_max_raw_roof_mph",
        "wind_mean_10m_mph",
        "wind_3s_gust_10m_mph",
        "wind_max_raw_10m_mph",
        "n_samples",
    ]
    summary = summary[column_order]

    return summary


def plot_summary(summary, name):
    plt.figure(figsize=(12, 5))

    plt.plot(
        summary["timestamp"],
        summary["wind_mean_10m_mph"],
        label="Mean wind speed at 10 m",
    )

    plt.plot(
        summary["timestamp"],
        summary["wind_3s_gust_10m_mph"],
        label="3-sec gust at 10 m",
        alpha=0.7,
    )

    plt.xlabel("Time")
    plt.ylabel("Wind speed [mph]")
    plt.title(f"Wind speed summary, height-corrected to 10 m - {name}")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()

    out_path = OUT_DIR / f"wind_summary_10m_mph_{name}.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def main():
    correction_factor = height_correction_factor()
    if ANEMOMETER_HEIGHT_M is None or REFERENCE_HEIGHT_M is None:
        print(
            "Height correction disabled (heights unset); "
            f"factor={correction_factor:.6f} (identity)"
        )
    else:
        print(
            "Height correction factor, "
            f"{ANEMOMETER_HEIGHT_M:.0f} m to {REFERENCE_HEIGHT_M:.0f} m, "
            f"exponent={WIND_PROFILE_EXPONENT}: {correction_factor:.6f}"
        )

    all_summaries = []

    for file_path in WIND_FILES:
        if not file_path.exists():
            print(f"Missing file: {file_path}")
            continue

        summary = summarize_file(file_path, window="30min")

        name = file_path.stem
        out_csv = OUT_DIR / f"wind_summary_{name}.csv"
        summary.to_csv(out_csv, index=False)
        print(f"Saved: {out_csv}")

        plot_summary(summary, name)

        all_summaries.append(summary)

    if all_summaries:
        combined = pd.concat(all_summaries, ignore_index=True)
        out_csv = OUT_DIR / "wind_summary_all.csv"
        combined.to_csv(out_csv, index=False)
        print(f"Saved: {out_csv}")


if __name__ == "__main__":
    main()
