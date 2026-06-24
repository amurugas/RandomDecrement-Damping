from pathlib import Path
import sys

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_sensor_file


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
    "29S2X-20230301_003526.txt",
    "29S2Y-20230301_003526.txt",
    "29S3X-20230301_003526.txt",
]

ETABS_MODES = {
    "M1 UX 6.87s": 6.87,
    "M2 RZ 5.95s": 5.95,
    "M3 UY 5.49s": 5.49,
    "M4 UX 2.71s": 2.71,
    "M5 RZ 2.28s": 2.28,
    "M6 UY 2.12s": 2.12,
}


def compute_psd(file_path, nperseg=131072):
    meta, df = read_sensor_file(file_path)

    x = df["accel_m_s2"].to_numpy()
    x = x - np.nanmean(x)

    fs = meta["sampling_rate_hz"]

    f, pxx = welch(
        x,
        fs=fs,
        nperseg=nperseg,
        detrend="constant",
        scaling="density",
    )

    return meta, f, pxx


def plot_group(files, title, output_name, xlim=(0.05, 0.50)):
    plt.figure(figsize=(12, 7))

    for file_name in files:
        file_path = RAW_DIR / file_name
        meta, f, pxx = compute_psd(file_path)

        label = meta["channel"]
        plt.semilogy(f, pxx, label=label)

    for label, period_sec in ETABS_MODES.items():
        freq_hz = 1.0 / period_sec
        plt.axvline(freq_hz, linestyle="--", linewidth=1.2, label=f"ETABS {label}")

    plt.xlim(*xlim)
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("PSD [(m/s²)²/Hz]")
    plt.title(title)
    plt.grid(True, which="both", alpha=0.35)
    plt.legend(fontsize=8, ncol=2)
    plt.tight_layout()

    out_path = OUT_DIR / output_name
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def main():
    x_files = [
        "21S2X-20230301_000511.txt",
        "25S2X-20230301_000511.txt",
        "29S2X-20230301_003526.txt",
    ]

    y_files = [
        "21S2Y-20230301_000511.txt",
        "25S2Y-20230301_000511.txt",
        "29S2Y-20230301_003526.txt",
    ]

    torsion_files = [
        "21S3X-20230301_000511.txt",
        "25S3X-20230301_000511.txt",
        "29S3X-20230301_003526.txt",
    ]

    plot_group(
        x_files,
        "Measured PSD with ETABS modal frequencies - X direction",
        "psd_x_direction.png",
    )

    plot_group(
        y_files,
        "Measured PSD with ETABS modal frequencies - Y direction",
        "psd_y_direction.png",
    )

    plot_group(
        torsion_files,
        "Measured PSD with ETABS modal frequencies - S3X / torsion-related channels",
        "psd_torsion_channels.png",
    )


if __name__ == "__main__":
    main()