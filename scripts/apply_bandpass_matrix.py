from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import welch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_sensor_file
from src.filtering import bandpass_filter
from src.config import (
    DATASETS,
    MEASURED_MODES,
    ETABS_MODES,
    BANDPASS_SENSITIVITY,
    ETABS_BANDPASS_CASES,
)


OUT_DIR = Path("results/bandpass_matrix")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_DIR = Path("data/processed_matrix")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def find_channel_file(folder, channel):
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
        nperseg=min(nperseg, len(x)),
        detrend="constant",
        scaling="density",
    )

    return f, pxx


def plot_psd_before_after(
    dataset,
    mode_name,
    band_name,
    channel,
    fs,
    raw,
    filtered,
    mode_frequency_hz,
    f_low,
    f_high,
):
    f_raw, p_raw = compute_psd(raw, fs)
    f_filt, p_filt = compute_psd(filtered, fs)

    plt.figure(figsize=(12, 7))

    plt.semilogy(f_raw, p_raw, label="Raw acceleration")
    plt.semilogy(f_filt, p_filt, label="Bandpassed acceleration", linewidth=2)

    plt.axvline(
        mode_frequency_hz,
        linestyle="--",
        linewidth=1.4,
        label=f"Target mode = {mode_frequency_hz:.3f} Hz",
    )

    plt.axvspan(
        f_low,
        f_high,
        alpha=0.15,
        label=f"Bandpass {f_low:.3f}–{f_high:.3f} Hz",
    )

    plt.xlim(0.05, 0.60)
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("PSD [(m/s²)²/Hz]")
    plt.title(f"{dataset} {channel} - {mode_name} - {band_name}")
    plt.grid(True, which="both", alpha=0.35)
    plt.legend(fontsize=9)
    plt.tight_layout()

    out_path = OUT_DIR / f"psd_{dataset}_{mode_name}_{band_name}_{channel}.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def process_bandpass_case(
    dataset,
    channels,
    mode_name,
    mode_frequency_hz,
    mode_period_sec,
    band_name,
    f_low,
    f_high,
):
    accel_folder = DATASETS[dataset]["accel_folder"]

    print("\n" + "=" * 100)
    print(f"Dataset: {dataset}")
    print(f"Mode: {mode_name}")
    print(f"Band: {band_name} = {f_low:.3f}–{f_high:.3f} Hz")
    print("=" * 100)

    for channel in channels:
        file_path = find_channel_file(accel_folder, channel)

        print(f"Reading {file_path}")

        meta, df = read_sensor_file(file_path)

        fs = meta["sampling_rate_hz"]
        raw = df["accel_m_s2"].to_numpy()
        raw = raw - np.nanmean(raw)

        filtered = bandpass_filter(
            raw,
            fs=fs,
            f_low=f_low,
            f_high=f_high,
            order=4,
        )

        safe_mode_name = mode_name.replace("/", "_")
        safe_band_name = band_name.replace("/", "_")

        out_npz = (
            PROCESSED_DIR
            / f"bandpassed_{dataset}_{safe_mode_name}_{safe_band_name}_{channel}.npz"
        )

        np.savez_compressed(
            out_npz,
            time_sec=df["time_sec"].to_numpy(),
            raw_accel_m_s2=raw,
            filtered_accel_m_s2=filtered,
            fs=fs,
            f_low=f_low,
            f_high=f_high,
            mode_name=mode_name,
            band_name=band_name,
            mode_frequency_hz=mode_frequency_hz,
            mode_period_sec=mode_period_sec,
            channel=channel,
            dataset=dataset,
        )

        print(f"Saved: {out_npz}")

        plot_psd_before_after(
            dataset=dataset,
            mode_name=safe_mode_name,
            band_name=safe_band_name,
            channel=channel,
            fs=fs,
            raw=raw,
            filtered=filtered,
            mode_frequency_hz=mode_frequency_hz,
            f_low=f_low,
            f_high=f_high,
        )


def run_measured_mode_bandpass_sensitivity():
    """
    Run narrow / medium / wide bandpass tests around measured FDD modes.
    """
    for mode_name, mode in MEASURED_MODES.items():
        dataset = mode["dataset"]
        channels = DATASETS[dataset]["sync_groups"]["L21_L25_6sync"]

        for band in BANDPASS_SENSITIVITY[mode_name]:
            process_bandpass_case(
                dataset=dataset,
                channels=channels,
                mode_name=mode_name,
                mode_frequency_hz=mode["frequency_hz"],
                mode_period_sec=mode["period_sec"],
                band_name=band["band_name"],
                f_low=band["f_low"],
                f_high=band["f_high"],
            )


def run_etabs_mode_cases():
    """
    Run bandpass filtering around ETABS-predicted modes for each dataset.
    """
    for dataset, dataset_info in DATASETS.items():
        channels = dataset_info["sync_groups"]["L25_3sync"]

        for mode_name, mode in ETABS_MODES.items():
            period_sec = mode["period_sec"]
            frequency_hz = 1.0 / period_sec

            band = ETABS_BANDPASS_CASES[mode_name]

            process_bandpass_case(
                dataset=dataset,
                channels=channels,
                mode_name=mode_name,
                mode_frequency_hz=frequency_hz,
                mode_period_sec=period_sec,
                band_name="default",
                f_low=band["f_low"],
                f_high=band["f_high"],
            )


def main():
    # 1. Sensitivity around measured modes
    run_measured_mode_bandpass_sensitivity()

    # 2. ETABS-predicted mode bands
    #run_etabs_mode_cases()


if __name__ == "__main__":
    main()