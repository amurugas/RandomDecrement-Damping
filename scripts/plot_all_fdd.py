from pathlib import Path
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_sensor_file
from src.fdd import build_csd_matrix, compute_fdd


OUT_DIR = Path("results")
OUT_DIR.mkdir(exist_ok=True)

ETABS_MODES = {
    "M1 UX 6.87s": 6.87,
    "M2 RZ 5.95s": 5.95,
    "M3 UY 5.49s": 5.49,
    "M4 UX 2.71s": 2.71,
    "M5 RZ 2.28s": 2.28,
    "M6 UY 2.12s": 2.12,
}


CASES = [
    {
        "dataset": "2023-03-01",
        "folder": Path("data/2023-03-01/Accelerometer"),
        "name": "2023_6sync_L21_L25",
        "title": "FDD - 2023-03-01 - synchronized 6 sensors, L21 + L25",
        "files": [
            "21S2X-20230301_000511.txt",
            "21S2Y-20230301_000511.txt",
            "21S3X-20230301_000511.txt",
            "25S2X-20230301_000511.txt",
            "25S2Y-20230301_000511.txt",
            "25S3X-20230301_000511.txt",

        ],
    },
    {
        "dataset": "2023-03-01",
        "folder": Path("data/2023-03-01/Accelerometer"),
        "name": "2023_3sync_L25",
        "title": "FDD - 2023-03-01 - synchronized 3 sensors, L25 only",
        "files": [
                "29S2X-20230301_003526.txt",
                "29S2Y-20230301_003526.txt",
                "29S3X-20230301_003526.txt",
        ],
    },
    {
        "dataset": "2025-12-27",
        "folder": Path("data/2025-12-27/Accelerometer"),
        "name": "2025_6sync_L21_L25",
        "title": "FDD - 2025-12-27 - synchronized 6 sensors, L21 + L25",
        "files": [
            "21S2X-20251227_000254.txt",
            "21S2Y-20251227_000254.txt",
            "21S3X-20251227_000254.txt",
            "25S2X-20251227_000254.txt",
            "25S2Y-20251227_000254.txt",
            "25S3X-20251227_000254.txt",
        ],
    },
    {
        "dataset": "2025-12-27",
        "folder": Path("data/2025-12-27/Accelerometer"),
        "name": "2025_3sync_L25",
        "title": "FDD - 2025-12-27 - synchronized 3 sensors, L25 only",
        "files": [
            "29S2X-20251227_003323.txt",
            "29S2Y-20251227_003323.txt",
            "29S3X-20251227_003323.txt",
        ],
    },
]


def load_case_signals(case):
    signals = {}
    fs_values = []

    for file_name in case["files"]:
        file_path = case["folder"] / file_name

        if not file_path.exists():
            raise FileNotFoundError(f"Missing file: {file_path}")

        print(f"Reading {file_path}")

        meta, df = read_sensor_file(file_path)

        channel = meta["channel"]
        x = df["accel_m_s2"].to_numpy()
        x = x - np.nanmean(x)

        signals[channel] = x
        fs_values.append(meta["sampling_rate_hz"])

        print(
            f"  {channel}: {meta.get('Start_date')} "
            f"{meta.get('Start_time')} | n={len(x):,}"
        )

    fs_values = np.array(fs_values)

    if not np.allclose(fs_values, fs_values[0]):
        raise ValueError(f"Sampling rates do not match: {fs_values}")

    min_len = min(len(x) for x in signals.values())
    signals = {ch: x[:min_len] for ch, x in signals.items()}

    print(f"Trimmed all channels to {min_len:,} samples")
    print(f"Duration = {min_len / fs_values[0] / 3600:.2f} hours")

    return signals, fs_values[0]

def plot_combined_first_singular_value(results, xlim=(0.05, 0.50)):
    plt.figure(figsize=(12, 7))

    for result in results:
        case = result["case"]
        f = result["freqs"]
        singular_values = result["singular_values"]

        plt.semilogy(
            f,
            singular_values[:, 0],
            linewidth=1.8,
            label=case["name"],
        )

    for label, period_sec in ETABS_MODES.items():
        freq_hz = 1.0 / period_sec
        plt.axvline(
            freq_hz,
            linestyle="--",
            linewidth=1.0,
            label=f"ETABS {label}",
        )

    plt.xlim(*xlim)
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("1st singular value of CSD matrix")
    plt.title("FDD comparison - 1st singular value")
    plt.grid(True, which="both", alpha=0.35)
    plt.legend(fontsize=8, ncol=2)
    plt.tight_layout()

    out_path = OUT_DIR / "fdd_comparison_first_singular_value.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def plot_case_fdd(case, f, singular_values, channels, xlim=(0.05, 0.50)):
    plt.figure(figsize=(12, 7))

    n_plot = min(3, singular_values.shape[1])

    for i in range(n_plot):
        plt.semilogy(
            f,
            singular_values[:, i],
            label=f"Singular value {i + 1}",
            alpha=1.0 if i == 0 else 0.75,
        )

    for label, period_sec in ETABS_MODES.items():
        freq_hz = 1.0 / period_sec
        plt.axvline(
            freq_hz,
            linestyle="--",
            linewidth=1.1,
            label=f"ETABS {label}",
        )

    plt.xlim(*xlim)
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Singular value of CSD matrix")
    plt.title(case["title"])
    plt.grid(True, which="both", alpha=0.35)
    plt.legend(fontsize=8, ncol=2)
    plt.tight_layout()

    out_path = OUT_DIR / f"fdd_{case['name']}.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")

    channels_path = OUT_DIR / f"channels_{case['name']}.txt"
    with channels_path.open("w", encoding="utf-8") as f_out:
        for i, ch in enumerate(channels):
            f_out.write(f"{i}: {ch}\n")

    print(f"Saved: {channels_path}")


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

    plot_case_fdd(case, freqs, singular_values, channels)

    return {
        "case": case,
        "freqs": freqs,
        "singular_values": singular_values,
        "channels": channels,
    }


def main():
    results = []

    for case in CASES:
        result = run_case(case)
        results.append(result)

    plot_combined_first_singular_value(results)

if __name__ == "__main__":
    main()