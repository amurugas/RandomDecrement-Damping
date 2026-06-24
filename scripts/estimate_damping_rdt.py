from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import decimate

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.rdt import random_decrement_signature
from src.damping import fit_exponential_decay


PROCESSED_DIR = Path("data/processed")
OUT_DIR = Path("results/rdt")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# Main RDT settings
TARGET_FS = 10.0              # Hz, enough for 0.2–0.4 Hz building modes
EDGE_TRIM_SECONDS = 60.0      # discard filter edge effects
SEGMENT_SECONDS = 90.0        # RDT decay length
THRESHOLD_FACTOR = 0.5        # trigger = 0.5 * std(filtered signal)


def get_scalar(npz, key):
    value = npz[key]
    if hasattr(value, "item"):
        return value.item()
    return value


def downsample_signal(x, fs, target_fs):
    """
    Downsample signal to target_fs if possible.
    """
    if fs <= target_fs:
        return x, fs

    q = int(round(fs / target_fs))

    if q <= 1:
        return x, fs

    fs_new = fs / q

    y = decimate(
        x,
        q=q,
        ftype="iir",
        zero_phase=True,
    )

    return y, fs_new


def estimate_file(npz_path):
    print("\n" + "=" * 80)
    print(npz_path.name)
    print("=" * 80)

    data = np.load(npz_path, allow_pickle=True)

    filtered = data["filtered_accel_m_s2"].astype(float)

    fs = float(get_scalar(data, "fs"))
    mode_frequency_hz = float(get_scalar(data, "mode_frequency_hz"))
    mode_period_sec = float(get_scalar(data, "mode_period_sec"))
    f_low = float(get_scalar(data, "f_low"))
    f_high = float(get_scalar(data, "f_high"))
    channel = str(get_scalar(data, "channel"))
    dataset = str(get_scalar(data, "dataset"))

    # Remove filter edge effects
    n_trim = int(round(EDGE_TRIM_SECONDS * fs))

    if len(filtered) <= 2 * n_trim:
        raise ValueError("Signal too short for requested edge trimming.")

    x = filtered[n_trim:-n_trim]
    x = x - np.nanmean(x)

    # Downsample to make RDT faster
    x_ds, fs_ds = downsample_signal(x, fs, TARGET_FS)

    print(f"Dataset: {dataset}")
    print(f"Channel: {channel}")
    print(f"Original fs: {fs:.2f} Hz")
    print(f"RDT fs: {fs_ds:.2f} Hz")
    print(f"Mode frequency: {mode_frequency_hz:.4f} Hz")
    print(f"Mode period: {mode_period_sec:.3f} sec")
    print(f"Bandpass: {f_low:.3f}–{f_high:.3f} Hz")

    # RDT settings tied to the mode
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

    # Fit approximately from 1 cycle to 12 cycles
    fit_start = 1.0 * mode_period_sec
    fit_end = min(12.0 * mode_period_sec, SEGMENT_SECONDS * 0.60)

    result = fit_exponential_decay(
        t=t_rdt,
        response=rds,
        natural_frequency_hz=mode_frequency_hz,
        fit_start=fit_start,
        fit_end=fit_end,
    )

    print(f"RDT segments: {n_segments}")
    print(f"Threshold: {threshold:.4e}")
    print(f"Damping ratio: {result['zeta']:.5f}")
    print(f"Damping percent: {result['damping_percent']:.2f}%")
    print(f"Fit R²: {result['r_squared']:.3f}")

    plot_rdt_result(
        npz_path=npz_path,
        dataset=dataset,
        channel=channel,
        mode_frequency_hz=mode_frequency_hz,
        mode_period_sec=mode_period_sec,
        t=t_rdt,
        rds=rds,
        result=result,
        n_segments=n_segments,
    )

    return {
        "file": npz_path.name,
        "dataset": dataset,
        "channel": channel,
        "mode_frequency_hz": mode_frequency_hz,
        "mode_period_sec": mode_period_sec,
        "f_low": f_low,
        "f_high": f_high,
        "fs_rdt_hz": fs_ds,
        "segment_seconds": SEGMENT_SECONDS,
        "threshold_factor": THRESHOLD_FACTOR,
        "threshold": threshold,
        "n_segments": n_segments,
        "fit_start_sec": fit_start,
        "fit_end_sec": fit_end,
        "alpha": result["alpha"],
        "damping_ratio": result["zeta"],
        "damping_percent": result["damping_percent"],
        "fit_r_squared": result["r_squared"],
    }


def plot_rdt_result(
    npz_path,
    dataset,
    channel,
    mode_frequency_hz,
    mode_period_sec,
    t,
    rds,
    result,
    n_segments,
):
    envelope = result["envelope"]
    envelope_fit = result["envelope_fit"]

    plt.figure(figsize=(12, 7))

    plt.plot(t, rds, label="Random Decrement Signature", linewidth=1.5)
    plt.plot(t, envelope, label="Hilbert envelope", linewidth=1.5)
    plt.plot(
        t,
        envelope_fit,
        "--",
        label="Exponential fit",
        linewidth=2,
    )

    plt.axvspan(
        result["fit_start"],
        result["fit_end"],
        alpha=0.15,
        label="Fit window",
    )

    plt.xlim(0, min(SEGMENT_SECONDS, 60))
    plt.xlabel("Time [sec]")
    plt.ylabel("Normalized response")
    plt.title(
        f"RDT damping estimate - {dataset} {channel}\\n"
        f"f = {mode_frequency_hz:.3f} Hz, "
        f"T = {mode_period_sec:.2f} sec, "
        f"ζ = {result['damping_percent']:.2f}%, "
        f"N = {n_segments}"
    )
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()

    out_name = npz_path.stem.replace("bandpassed_", "rdt_decay_") + ".png"
    out_path = OUT_DIR / out_name

    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def main():
    files = sorted(PROCESSED_DIR.glob("bandpassed_*.npz"))

    if not files:
        raise FileNotFoundError(f"No bandpassed files found in {PROCESSED_DIR}")

    rows = []

    for file in files:
        try:
            row = estimate_file(file)
            rows.append(row)
        except Exception as e:
            print(f"FAILED: {file.name}")
            print(e)

    df = pd.DataFrame(rows)

    out_csv = OUT_DIR / "damping_summary.csv"
    df.to_csv(out_csv, index=False)

    print("\nSaved:", out_csv)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()