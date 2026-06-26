from pathlib import Path
import sys

import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_wind_file

# Wind sensor / profile constants.
SENSOR_HEIGHT_M = 118.0
REFERENCE_HEIGHT_M = 10.0
WIND_PROFILE_ALPHA = 0.14
MPH_PER_MPS = 2.2369362920544
GUST_AVERAGING_SECONDS = 3.0

WIND_FILES = [
    Path("data/2023-03-01/Wind Sensor/08N4S-20230301_005350.txt"),
    Path("data/2025-12-27/Wind Sensor/31S4S-20251227_000722.txt"),
    # Update these filenames to match your actual files.
]

OUT_DIR = Path("results/wind")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def height_correct_to_reference(speed, sensor_height_m, reference_height_m, alpha):
    """
    Convert a wind speed measured at ``sensor_height_m`` to the equivalent
    speed at ``reference_height_m`` using a power-law (Exposure C) profile.

        V_ref = V_sensor * (reference_height_m / sensor_height_m) ** alpha
    """
    return speed * (reference_height_m / sensor_height_m) ** alpha


def summarize_file(file_path, window="30min"):
    print(f"Reading {file_path}")

    meta, df = read_wind_file(file_path)

    # Original sampling rate from metadata drives the 3-second gust window.
    fs = float(meta["sampling_rate_hz"])
    gust_window_samples = max(1, int(round(GUST_AVERAGING_SECONDS * fs)))

    df = df.set_index("timestamp")

    # Rolling 3-second average wind speed from the raw (roof-level) signal.
    df["wind_3s_avg_roof_m_s"] = (
        df["wind_m_s"].rolling(window=gust_window_samples, min_periods=1).mean()
    )

    grouped = df.resample(window)

    summary = grouped["wind_m_s"].agg(
        wind_mean_roof_m_s="mean",
        wind_median_roof_m_s="median",
        wind_max_raw_roof_m_s="max",
        wind_std_roof_m_s="std",
        n_samples="count",
    )

    # 3-second gust is the peak rolling 3-second average within each window.
    summary["wind_3s_gust_roof_m_s"] = grouped["wind_3s_avg_roof_m_s"].max()

    summary = summary.reset_index()

    summary["dataset"] = meta["Start_date"]
    summary["channel"] = meta["channel"]
    summary["window"] = window
    summary["sensor_height_m"] = SENSOR_HEIGHT_M
    summary["reference_height_m"] = REFERENCE_HEIGHT_M
    summary["wind_profile_alpha"] = WIND_PROFILE_ALPHA

    # Height-correct each roof-level statistic to the 10 m reference height.
    roof_to_10m = [
        ("wind_mean_roof_m_s", "wind_mean_10m_m_s"),
        ("wind_median_roof_m_s", "wind_median_10m_m_s"),
        ("wind_max_raw_roof_m_s", "wind_max_raw_10m_m_s"),
        ("wind_std_roof_m_s", "wind_std_10m_m_s"),
        ("wind_3s_gust_roof_m_s", "wind_3s_gust_10m_m_s"),
    ]
    for roof_col, ref_col in roof_to_10m:
        summary[ref_col] = height_correct_to_reference(
            summary[roof_col],
            SENSOR_HEIGHT_M,
            REFERENCE_HEIGHT_M,
            WIND_PROFILE_ALPHA,
        )

    # Convenient mph columns for both roof and 10 m corrected speeds.
    summary["wind_mean_roof_mph"] = summary["wind_mean_roof_m_s"] * MPH_PER_MPS
    summary["wind_3s_gust_roof_mph"] = summary["wind_3s_gust_roof_m_s"] * MPH_PER_MPS
    summary["wind_max_raw_roof_mph"] = summary["wind_max_raw_roof_m_s"] * MPH_PER_MPS
    summary["wind_mean_10m_mph"] = summary["wind_mean_10m_m_s"] * MPH_PER_MPS
    summary["wind_3s_gust_10m_mph"] = summary["wind_3s_gust_10m_m_s"] * MPH_PER_MPS
    summary["wind_max_raw_10m_mph"] = summary["wind_max_raw_10m_m_s"] * MPH_PER_MPS

    column_order = [
        "timestamp",
        "dataset",
        "channel",
        "window",
        "sensor_height_m",
        "reference_height_m",
        "wind_profile_alpha",
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
    correction_factor = (REFERENCE_HEIGHT_M / SENSOR_HEIGHT_M) ** WIND_PROFILE_ALPHA
    print(
        "Height correction factor, "
        f"{SENSOR_HEIGHT_M:.0f} m to {REFERENCE_HEIGHT_M:.0f} m, "
        f"alpha={WIND_PROFILE_ALPHA}: {correction_factor:.6f}"
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
