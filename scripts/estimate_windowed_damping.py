from pathlib import Path
import sys
from datetime import timedelta

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import decimate

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_sensor_metadata, parse_start_datetime
from src.rdt import random_decrement_signature
from src.damping import fit_exponential_decay


PROCESSED_DIR = Path("data/processed")
WIND_SUMMARY_FILE = Path("results/wind/wind_summary_all.csv")
OUT_DIR = Path("results/windowed_damping")
OUT_DIR.mkdir(parents=True, exist_ok=True)

WINDOW_SECONDS = 30 * 60
TARGET_FS = 10.0
SEGMENT_SECONDS = 90.0
THRESHOLD_FACTOR = 0.5
MIN_SEGMENTS = 100
MIN_R2 = 0.50


DATASET_FOLDERS = {
    "2023-03-01": Path("data/2023-03-01/Accelerometer"),
    "2025-12-27": Path("data/2025-12-27/Accelerometer"),
}


def get_scalar(npz, key):
    value = npz[key]
    if hasattr(value, "item"):
        return value.item()
    return value


def find_raw_accel_file(dataset, channel):
    folder = DATASET_FOLDERS[dataset]
    matches = sorted(folder.glob(f"{channel}-*.txt"))

    if not matches:
        raise FileNotFoundError(f"No raw file found for {dataset} {channel}")

    return matches[0]


def get_accel_start_datetime(dataset, channel):
    raw_file = find_raw_accel_file(dataset, channel)
    meta = read_sensor_metadata(raw_file)
    return parse_start_datetime(meta)


def downsample_signal(x, fs, target_fs):
    if fs <= target_fs:
        return x, fs

    q = int(round(fs / target_fs))

    if q <= 1:
        return x, fs

    y = decimate(
        x,
        q=q,
        ftype="iir",
        zero_phase=True,
    )

    fs_new = fs / q

    return y, fs_new


def estimate_window_damping(x_window, fs, mode_frequency_hz, mode_period_sec):
    x_window = np.asarray(x_window, dtype=float)
    x_window = x_window - np.nanmean(x_window)

    x_ds, fs_ds = downsample_signal(x_window, fs, TARGET_FS)

    min_spacing_seconds = 0.8 * mode_period_sec

    t_rdt, rds, n_segments, threshold = random_decrement_signature(
        signal=x_ds,
        fs=fs_ds,
        segment_seconds=SEGMENT_SECONDS,
        threshold=None,
        threshold_factor=THRESHOLD_FACTOR,
        min_spacing_seconds=min_spacing_seconds,
        normalize=True,
    )

    fit_start = 1.0 * mode_period_sec
    fit_end = min(8.0 * mode_period_sec, SEGMENT_SECONDS * 0.50)

    result = fit_exponential_decay(
        t=t_rdt,
        response=rds,
        natural_frequency_hz=mode_frequency_hz,
        fit_start=fit_start,
        fit_end=fit_end,
    )

    return {
        "fs_rdt_hz": fs_ds,
        "n_segments": n_segments,
        "threshold": threshold,
        "fit_start_sec": fit_start,
        "fit_end_sec": fit_end,
        "alpha": result["alpha"],
        "damping_ratio": result["zeta"],
        "damping_percent": result["damping_percent"],
        "fit_r_squared": result["r_squared"],
    }


def load_wind_summary():
    wind = pd.read_csv(WIND_SUMMARY_FILE)

    wind["timestamp"] = pd.to_datetime(wind["timestamp"])

    return wind


def process_bandpassed_file(npz_path, wind):
    data = np.load(npz_path, allow_pickle=True)

    dataset = str(get_scalar(data, "dataset"))
    channel = str(get_scalar(data, "channel"))

    filtered = data["filtered_accel_m_s2"].astype(float)
    fs = float(get_scalar(data, "fs"))
    mode_frequency_hz = float(get_scalar(data, "mode_frequency_hz"))
    mode_period_sec = float(get_scalar(data, "mode_period_sec"))
    f_low = float(get_scalar(data, "f_low"))
    f_high = float(get_scalar(data, "f_high"))

    accel_start = get_accel_start_datetime(dataset, channel)
    accel_end = accel_start + timedelta(seconds=len(filtered) / fs)

    print("\n" + "=" * 80)
    print(npz_path.name)
    print(f"Dataset: {dataset}")
    print(f"Channel: {channel}")
    print(f"Accel start: {accel_start}")
    print(f"Accel end:   {accel_end}")
    print("=" * 80)

    # Use wind rows that overlap this acceleration record
    w = wind[
        (wind["timestamp"] >= accel_start)
        & (wind["timestamp"] < accel_end)
    ].copy()

    if w.empty:
        print("No overlapping wind windows.")
        return []

    rows = []

    for _, row in w.iterrows():
        window_start = row["timestamp"].to_pydatetime()
        window_end = window_start + timedelta(seconds=WINDOW_SECONDS)

        if window_end > accel_end:
            continue

        t0 = (window_start - accel_start).total_seconds()
        t1 = (window_end - accel_start).total_seconds()

        i0 = int(round(t0 * fs))
        i1 = int(round(t1 * fs))

        x_window = filtered[i0:i1]

        if len(x_window) < fs * WINDOW_SECONDS * 0.95:
            continue

        try:
            est = estimate_window_damping(
                x_window=x_window,
                fs=fs,
                mode_frequency_hz=mode_frequency_hz,
                mode_period_sec=mode_period_sec,
            )

            quality_flag = (
                est["n_segments"] >= MIN_SEGMENTS
                and est["fit_r_squared"] >= MIN_R2
                and np.isfinite(est["damping_percent"])
                and est["damping_percent"] > 0
            )

            output_row = {
                "file": npz_path.name,
                "dataset": dataset,
                "channel": channel,
                "window_start": window_start,
                "window_end": window_end,
                "mode_frequency_hz": mode_frequency_hz,
                "mode_period_sec": mode_period_sec,
                "f_low": f_low,
                "f_high": f_high,
                "wind_mean_m_s": row.get("wind_mean_m_s", np.nan),
                "wind_median_m_s": row.get("wind_median_m_s", np.nan),
                "wind_max_m_s": row.get("wind_max_m_s", np.nan),
                "wind_std_m_s": row.get("wind_std_m_s", np.nan),
                "wind_mean_mph": row.get("wind_mean_mph", np.nan),
                "wind_median_mph": row.get("wind_median_mph", np.nan),
                "wind_max_mph": row.get("wind_max_mph", np.nan),
                "wind_std_mph": row.get("wind_std_mph", np.nan),
                "wind_n_samples": row.get("n_samples", np.nan),
                "quality_flag": quality_flag,
            }

            output_row.update(est)
            rows.append(output_row)

            print(
                f"{window_start} | "
                f"wind_mean={output_row['wind_mean_m_s']:.2f} m/s | "
                f"zeta={output_row['damping_percent']:.2f}% | "
                f"R2={output_row['fit_r_squared']:.2f} | "
                f"N={output_row['n_segments']}"
            )

        except Exception as e:
            print(f"Window failed: {window_start} | {e}")

    return rows


def plot_damping_vs_wind(df):
    good = df[df["quality_flag"] == True].copy()

    if good.empty:
        print("No good-quality damping windows to plot.")
        return

    plt.figure(figsize=(10, 6))

    for (dataset, channel), g in good.groupby(["dataset", "channel"]):
        plt.scatter(
            g["wind_mean_mph"],
            g["damping_percent"],
            label=f"{dataset} {channel}",
            alpha=0.75,
        )

    plt.xlabel("Mean wind speed [mph]")
    plt.ylabel("RDT damping estimate [%]")
    plt.title("Windowed damping vs mean wind speed")
    plt.grid(True, alpha=0.35)
    plt.legend(fontsize=8)
    plt.tight_layout()

    out_path = OUT_DIR / "damping_vs_mean_wind_speed_mph.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def plot_damping_time_history(df):
    good = df[df["quality_flag"] == True].copy()

    if good.empty:
        print("No good-quality damping windows to plot.")
        return

    for dataset, g_dataset in good.groupby("dataset"):
        plt.figure(figsize=(12, 5))

        for channel, g in g_dataset.groupby("channel"):
            plt.plot(
                g["window_start"],
                g["damping_percent"],
                marker="o",
                label=channel,
            )

        plt.xlabel("Time")
        plt.ylabel("RDT damping estimate [%]")
        plt.title(f"Windowed damping time history - {dataset}")
        plt.grid(True, alpha=0.35)
        plt.legend()
        plt.tight_layout()

        out_path = OUT_DIR / f"damping_time_history_{dataset}.png"
        plt.savefig(out_path, dpi=300)
        plt.close()

        print(f"Saved: {out_path}")


def main():
    wind = load_wind_summary()

    files = sorted(PROCESSED_DIR.glob("bandpassed_*.npz"))

    if not files:
        raise FileNotFoundError(f"No bandpassed files found in {PROCESSED_DIR}")

    all_rows = []

    for file in files:
        rows = process_bandpassed_file(file, wind)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)

    out_csv = OUT_DIR / "windowed_damping_summary.csv"
    df.to_csv(out_csv, index=False)

    print(f"\nSaved: {out_csv}")

    if not df.empty:
        print(df.to_string(index=False))
        plot_damping_vs_wind(df)
        plot_damping_time_history(df)


if __name__ == "__main__":
    main()