from pathlib import Path
import sys

import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_wind_file
from src.wind import mps_to_mph

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

    df = df.set_index("timestamp")

    # wind_ref_m_s is already reference-height corrected at read time.
    summary = df["wind_ref_m_s"].resample(window).agg(
        wind_mean_m_s="mean",
        wind_median_m_s="median",
        wind_max_m_s="max",
        wind_std_m_s="std",
        n_samples="count",
    )

    summary = summary.reset_index()
    summary["dataset"] = meta["Start_date"]
    summary["channel"] = meta["channel"]
    summary["window"] = window

    summary["wind_mean_mph"] = mps_to_mph(summary["wind_mean_m_s"])
    summary["wind_median_mph"] = mps_to_mph(summary["wind_median_m_s"])
    summary["wind_max_mph"] = mps_to_mph(summary["wind_max_m_s"])
    summary["wind_std_mph"] = mps_to_mph(summary["wind_std_m_s"])

    return summary


def plot_summary(summary, name):
    plt.figure(figsize=(12, 5))

    plt.plot(
        summary["timestamp"],
        summary["wind_mean_mph"],
        label="Mean wind speed",
    )

    plt.plot(
        summary["timestamp"],
        summary["wind_max_mph"],
        label="Max wind speed",
        alpha=0.7,
    )

    plt.xlabel("Time")
    plt.ylabel("Wind speed [mph]")
    plt.title(f"Wind speed summary - {name}")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()

    out_path = OUT_DIR / f"wind_summary_mph_{name}.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def main():
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