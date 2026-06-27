from pathlib import Path
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_sensor_file
from src.fdd import build_csd_matrix, compute_fdd


RAW_DIR = Path("data/2023-03-01/Accelerometer")
OUT_DIR = Path("results")
OUT_DIR.mkdir(exist_ok=True)

FILES = [
    "21S2X-20230301_000511.txt",
    "21S2Y-20230301_000511.txt",
    "21S3X-20230301_000511.txt",
    "25S2X-20230301_000511.txt",
    "25S2Y-20230301_000511.txt",
    "25S3X-20230301_000511.txt",
#    "29S2X-20230301_003526.txt",
#    "29S2Y-20230301_003526.txt",
#    "29S3X-20230301_003526.txt",
]

ETABS_MODES = {
    "M1 UX 6.87s": 6.87,
    "M2 RZ 5.95s": 5.95,
    "M3 UY 5.49s": 5.49,
    "M4 UX 2.71s": 2.71,
    "M5 RZ 2.28s": 2.28,
    "M6 UY 2.12s": 2.12,
}


def load_all_signals():
    signals = {}
    fs_values = []

    for file_name in FILES:
        file_path = RAW_DIR / file_name
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

    # Trim all channels to same length
    min_len = min(len(x) for x in signals.values())
    signals = {ch: x[:min_len] for ch, x in signals.items()}

    return signals, fs_values[0]


def plot_fdd(f, singular_values):
    plt.figure(figsize=(12, 7))

    plt.semilogy(f, singular_values[:, 0], label="1st singular value")
    plt.semilogy(f, singular_values[:, 1], label="2nd singular value", alpha=0.7)
    plt.semilogy(f, singular_values[:, 2], label="3rd singular value", alpha=0.7)

    for label, period_sec in ETABS_MODES.items():
        freq_hz = 1.0 / period_sec
        plt.axvline(freq_hz, linestyle="--", linewidth=1.2, label=f"ETABS {label}")

    plt.xlim(0.05, 0.50)
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Singular value of CSD matrix")
    plt.title("Frequency Domain Decomposition - all 9 sensors")
    plt.grid(True, which="both", alpha=0.35)
    plt.legend(fontsize=8, ncol=2)
    plt.tight_layout()

    out_path = OUT_DIR / "fdd_all_9_sensors.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def main():
    signals, fs = load_all_signals()

    print("Building CSD matrix...")
    f, G, channels = build_csd_matrix(
        signals,
        fs=fs,
        nperseg=131072,
        noverlap=65536,
    )

    print("Running SVD...")
    singular_values, mode_shapes = compute_fdd(G)

    plot_fdd(f, singular_values)

    print("Channel order:")
    for i, ch in enumerate(channels):
        print(f"{i}: {ch}")


if __name__ == "__main__":
    main()