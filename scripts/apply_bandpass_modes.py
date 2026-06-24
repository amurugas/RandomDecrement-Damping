from pathlib import Path
import sys

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_sensor_file
from src.filtering import bandpass_filter


OUT_DIR = Path("results/bandpass")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


MODAL_CASES = [
    {
        "dataset": "2023-03-01",
        "folder": Path("data/2023-03-01/Accelerometer"),
        "name": "2023_mode_3p62s",
        "mode_period_sec": 3.62,
        "mode_frequency_hz": 1.0 / 3.62,
        "f_low": 0.23,
        "f_high": 0.33,
        "channels": ["25S2X", "25S2Y", "25S3X"],
    },
    {
        "dataset": "2025-12-27",
        "folder": Path("data/2025-12-27/Accelerometer"),
        "name": "2025_mode_3p01s",
        "mode_period_sec": 3.01,
        "mode_frequency_hz": 1.0 / 3.01,
        "f_low": 0.28,
        "f_high": 0.38,
        "channels": ["25S2X", "25S2Y", "25S3X"],
    },
]


def find_channel_file(folder, channel):
    """
    Find a raw file for a given channel, e.g. 25S2X-*.txt.
    """
    matches = sorted(folder.glob(f"{channel}-*.txt"))

    if not matches:
        raise FileNotFoundError(f"No file found for channel {channel} in {folder}")

    if len(matches) > 1:
        print(f"Warning: multiple files found for {channel}. Using {matches[0]}")

    return matches[0]


def compute_psd(x, fs, nperseg=131072):
    x = np.asarray(x, dtype=float)
    x = x - np.nanmean(x)

    f, pxx = welch(
        x,
        fs=fs,
        nperseg=nperseg,
        detrend="constant",
        scaling="density",
    )

    return f, pxx


def plot_psd_before_after(case, channel, fs, raw, filtered):
    f_raw, p_raw = compute_psd(raw, fs)
    f_filt, p_filt = compute_psd(filtered, fs)

    plt.figure(figsize=(12, 7))

    plt.semilogy(f_raw, p_raw, label="Raw acceleration")
    plt.semilogy(f_filt, p_filt, label="Bandpassed acceleration", linewidth=2)

    plt.axvline(
        case["mode_frequency_hz"],
        linestyle="--",
        linewidth=1.4,
        label=f"Measured mode = {case['mode_frequency_hz']:.3f} Hz",
    )

    plt.axvspan(
        case["f_low"],
        case["f_high"],
        alpha=0.15,
        label=f"Bandpass {case['f_low']:.2f}–{case['f_high']:.2f} Hz",
    )

    plt.xlim(0.05, 0.60)
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("PSD [(m/s²)²/Hz]")
    plt.title(f"{case['dataset']} {channel} - PSD before/after bandpass")
    plt.grid(True, which="both", alpha=0.35)
    plt.legend(fontsize=9)
    plt.tight_layout()

    out_path = OUT_DIR / f"psd_before_after_{case['name']}_{channel}.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def plot_time_preview(case, channel, fs, raw, filtered, start_sec=0, duration_sec=600):
    """
    Save a time-history preview. Default is first 10 minutes.
    """
    i0 = int(start_sec * fs)
    i1 = int((start_sec + duration_sec) * fs)

    raw_seg = raw[i0:i1]
    filt_seg = filtered[i0:i1]
    t = np.arange(len(filt_seg)) / fs + start_sec

    plt.figure(figsize=(12, 6))

    plt.plot(t, raw_seg, label="Raw acceleration", alpha=0.55)
    plt.plot(t, filt_seg, label="Bandpassed acceleration", linewidth=1.7)

    plt.xlabel("Time [sec]")
    plt.ylabel("Acceleration [m/s²]")
    plt.title(
        f"{case['dataset']} {channel} - bandpassed time history "
        f"({case['f_low']:.2f}–{case['f_high']:.2f} Hz)"
    )
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()

    out_path = OUT_DIR / f"time_preview_{case['name']}_{channel}.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def process_case(case):
    print("\n" + "=" * 80)
    print(case["name"])
    print("=" * 80)

    for channel in case["channels"]:
        file_path = find_channel_file(case["folder"], channel)
        print(f"Reading {file_path}")

        meta, df = read_sensor_file(file_path)

        fs = meta["sampling_rate_hz"]

        raw = df["accel_m_s2"].to_numpy()
        raw = raw - np.nanmean(raw)

        print(
            f"Filtering {channel}: "
            f"{case['f_low']:.3f}–{case['f_high']:.3f} Hz | "
            f"fs = {fs:.1f} Hz | n = {len(raw):,}"
        )

        filtered = bandpass_filter(
            raw,
            fs=fs,
            f_low=case["f_low"],
            f_high=case["f_high"],
            order=4,
        )

        out_npz = PROCESSED_DIR / f"bandpassed_{case['name']}_{channel}.npz"

        np.savez_compressed(
            out_npz,
            time_sec=df["time_sec"].to_numpy(),
            raw_accel_m_s2=raw,
            filtered_accel_m_s2=filtered,
            fs=fs,
            f_low=case["f_low"],
            f_high=case["f_high"],
            mode_frequency_hz=case["mode_frequency_hz"],
            mode_period_sec=case["mode_period_sec"],
            channel=channel,
            dataset=case["dataset"],
        )

        print(f"Saved: {out_npz}")

        plot_psd_before_after(case, channel, fs, raw, filtered)
        plot_time_preview(case, channel, fs, raw, filtered)


def main():
    for case in MODAL_CASES:
        process_case(case)


if __name__ == "__main__":
    main()