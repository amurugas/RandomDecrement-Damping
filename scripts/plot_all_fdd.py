from pathlib import Path
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_sensor_file
from src.fdd import build_csd_matrix, compute_fdd
from src.config import DATASETS
from src.io import parse_start_datetime
from src.alignment import SignalRecord, align_signal_records


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


def build_cases():
    cases = []

    for dataset, info in DATASETS.items():
        label = dataset[:4]
        groups = info["sync_groups"]
        l21_l25 = groups["L21_L25_6sync"]
        l29_roof = groups["L29_roof_3sync"]

        cases.extend(
            [
                {
                    "dataset": dataset,
                    "folder": info["accel_folder"],
                    "name": f"{label}_6sync_L21_L25",
                    "title": f"FDD - {dataset} - synchronized 6 sensors, L21 + L25",
                    "channels": l21_l25,
                    "align_by_time": False,
                },
                {
                    "dataset": dataset,
                    "folder": info["accel_folder"],
                    "name": f"{label}_3sync_L29_roof",
                    "title": (
                        f"FDD - {dataset} - synchronized 3 sensors, "
                        "Level 29 / Roof"
                    ),
                    "channels": l29_roof,
                    "align_by_time": False,
                },
                {
                    "dataset": dataset,
                    "folder": info["accel_folder"],
                    "name": f"{label}_9ch_aligned_L21_L25_L29_roof",
                    "title": (
                        f"FDD - {dataset} - aligned 9 sensors, "
                        "L21 + L25 + Level 29 / Roof"
                    ),
                    "channels": l21_l25 + l29_roof,
                    "align_by_time": True,
                },
            ]
        )

    return cases


CASES = build_cases()


def find_channel_file(folder, channel):
    matches = sorted(folder.glob(f"{channel}-*.txt"))

    if not matches:
        raise FileNotFoundError(f"No file found for channel {channel} in {folder}")

    if len(matches) > 1:
        print(f"Warning: multiple files found for {channel}. Using {matches[0]}")

    return matches[0]


def load_case_signals(case):
    records = []
    channels = case.get("channels")
    file_names = case.get("files")

    if channels is None and file_names is None:
        raise ValueError("Case must define either 'channels' or 'files'")

    file_refs = channels if channels is not None else file_names

    for file_ref in file_refs:
        if channels is not None:
            file_path = find_channel_file(case["folder"], file_ref)
        else:
            file_path = case["folder"] / file_ref

        if not file_path.exists():
            raise FileNotFoundError(f"Missing file: {file_path}")

        print(f"Reading {file_path}")

        meta, df = read_sensor_file(file_path)

        x = df["accel_m_s2"].to_numpy()
        start_time = parse_start_datetime(meta)

        print(
            f"  {meta['channel']}: {meta.get('Start_date')} "
            f"{meta.get('Start_time')} | n={len(x):,}"
        )

        records.append(
            SignalRecord(
                channel=meta["channel"],
                values=x,
                fs=meta["sampling_rate_hz"],
                start_time=start_time,
            )
        )

    signals, fs, alignment = align_signal_records(
        records,
        align_by_time=case.get("align_by_time", False),
    )
    signals = {
        channel: x - np.nanmean(x)
        for channel, x in signals.items()
    }

    if case.get("align_by_time", False):
        print("Alignment summary:")
        for channel in signals:
            item = alignment[channel]
            print(
                f"  {channel}: start={item['start_time']} "
                f"offset={item['offset_sec']:.3f}s "
                f"samples={item['source_start_index']}:{item['source_end_index']}"
            )

    n_samples = min(len(x) for x in signals.values())
    print(f"Aligned all channels to {n_samples:,} samples")
    print(f"Duration = {n_samples / fs / 3600:.2f} hours")

    return signals, fs

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
