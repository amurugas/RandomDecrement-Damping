from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_sensor_file
from src.fdd import build_csd_matrix, compute_fdd
from scripts.plot_all_fdd import CASES, ETABS_MODES


OUT_DIR = Path("results")
OUT_DIR.mkdir(exist_ok=True)


def load_case_signals(case):
    signals = {}
    fs_values = []

    for file_name in case["files"]:
        file_path = case["folder"] / file_name

        print(f"Reading {file_path}")
        meta, df = read_sensor_file(file_path)

        channel = meta["channel"]
        x = df["accel_m_s2"].to_numpy()
        x = x - np.nanmean(x)

        signals[channel] = x
        fs_values.append(meta["sampling_rate_hz"])

    fs_values = np.array(fs_values)

    if not np.allclose(fs_values, fs_values[0]):
        raise ValueError(f"Sampling rates do not match: {fs_values}")

    min_len = min(len(x) for x in signals.values())
    signals = {ch: x[:min_len] for ch, x in signals.items()}

    return signals, fs_values[0]


def closest_etabs_mode(freq_hz):
    closest_label = None
    closest_period = None
    closest_freq = None
    min_error = np.inf

    for label, period_sec in ETABS_MODES.items():
        etabs_freq = 1.0 / period_sec
        error = abs(freq_hz - etabs_freq)

        if error < min_error:
            min_error = error
            closest_label = label
            closest_period = period_sec
            closest_freq = etabs_freq

    return closest_label, closest_period, closest_freq, min_error


def extract_peaks(freqs, singular_value, case_name, fmin=0.05, fmax=0.50, max_peaks=5):
    mask = (freqs >= fmin) & (freqs <= fmax)

    f_use = freqs[mask]
    s_use = singular_value[mask]

    peaks, properties = find_peaks(
        s_use,
        prominence=np.nanmax(s_use) * 0.03,
        distance=5,
    )

    peak_freqs = f_use[peaks]
    peak_values = s_use[peaks]

    order = np.argsort(peak_values)[::-1]

    rows = []

    for rank, idx in enumerate(order[:max_peaks], start=1):
        freq_hz = peak_freqs[idx]
        period_sec = 1.0 / freq_hz
        peak_value = peak_values[idx]

        etabs_label, etabs_period, etabs_freq, freq_error = closest_etabs_mode(freq_hz)

        rows.append(
            {
                "case": case_name,
                "rank": rank,
                "measured_frequency_hz": freq_hz,
                "measured_period_sec": period_sec,
                "singular_value": peak_value,
                "closest_etabs_mode": etabs_label,
                "closest_etabs_frequency_hz": etabs_freq,
                "closest_etabs_period_sec": etabs_period,
                "frequency_error_hz": freq_error,
                "period_error_sec": abs(period_sec - etabs_period),
            }
        )

    return rows


def run_case(case):
    print("\n" + "=" * 80)
    print(case["name"])
    print("=" * 80)

    signals, fs = load_case_signals(case)

    print("Building CSD matrix...")
    freqs, G, channels = build_csd_matrix(
        signals,
        fs=fs,
        nperseg=131072,
        noverlap=65536,
    )

    print("Running SVD...")
    singular_values, mode_shapes = compute_fdd(G)

    first_sv = singular_values[:, 0]

    rows = extract_peaks(
        freqs,
        first_sv,
        case_name=case["name"],
        fmin=0.05,
        fmax=0.50,
        max_peaks=5,
    )

    return rows


def main():
    all_rows = []

    for case in CASES:
        rows = run_case(case)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)

    out_csv = OUT_DIR / "fdd_peak_summary.csv"
    df.to_csv(out_csv, index=False)

    print(f"\nSaved: {out_csv}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()