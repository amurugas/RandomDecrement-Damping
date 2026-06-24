from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


INPUT_CSV = Path("results/rdt/damping_summary.csv")
OUT_DIR = Path("results/sensitivity")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    df = pd.read_csv(INPUT_CSV)

    df = df[
        np.isfinite(df["damping_percent"])
        & (df["damping_percent"] > 0)
        & (df["damping_percent"] < 20)
        & (df["fit_r_squared"] >= 0.70)
    ].copy()

    return df


def summarize_sensitivity(df):
    group_cols = [
        "dataset",
        "mode_name",
        "band_name",
    ]

    summary = (
        df.groupby(group_cols)
        .agg(
            n_channels=("channel", "count"),
            damping_mean_percent=("damping_percent", "mean"),
            damping_median_percent=("damping_percent", "median"),
            damping_min_percent=("damping_percent", "min"),
            damping_max_percent=("damping_percent", "max"),
            damping_std_percent=("damping_percent", "std"),
            mean_r2=("fit_r_squared", "mean"),
            min_r2=("fit_r_squared", "min"),
            mean_segments=("n_segments", "mean"),
        )
        .reset_index()
    )

    return summary


def plot_measured_mode_sensitivity(summary):
    measured = summary[summary["mode_name"].str.startswith("measured")].copy()

    if measured.empty:
        print("No measured mode sensitivity data found.")
        return

    for dataset, g in measured.groupby("dataset"):
        plt.figure(figsize=(10, 6))

        for mode_name, gm in g.groupby("mode_name"):
            plt.errorbar(
                gm["band_name"],
                gm["damping_median_percent"],
                yerr=[
                    gm["damping_median_percent"] - gm["damping_min_percent"],
                    gm["damping_max_percent"] - gm["damping_median_percent"],
                ],
                fmt="o-",
                capsize=4,
                label=mode_name,
            )

        plt.xlabel("Bandpass case")
        plt.ylabel("Damping estimate [%]")
        plt.title(f"Bandpass sensitivity - {dataset}")
        plt.grid(True, alpha=0.35)
        plt.legend()
        plt.tight_layout()

        out_path = OUT_DIR / f"bandpass_sensitivity_{dataset}.png"
        plt.savefig(out_path, dpi=300)
        plt.close()

        print(f"Saved: {out_path}")


def plot_etabs_mode_damping(summary):
    etabs = summary[summary["mode_name"].str.startswith("ETABS")].copy()

    if etabs.empty:
        print("No ETABS mode damping data found.")
        return

    for dataset, g in etabs.groupby("dataset"):
        plt.figure(figsize=(12, 6))

        plt.bar(
            g["mode_name"],
            g["damping_median_percent"],
        )

        plt.xticks(rotation=45, ha="right")
        plt.xlabel("ETABS mode")
        plt.ylabel("Median RDT damping estimate [%]")
        plt.title(f"RDT damping around ETABS-predicted modes - {dataset}")
        plt.grid(True, axis="y", alpha=0.35)
        plt.tight_layout()

        out_path = OUT_DIR / f"etabs_mode_damping_{dataset}.png"
        plt.savefig(out_path, dpi=300)
        plt.close()

        print(f"Saved: {out_path}")


def main():
    df = load_data()

    summary = summarize_sensitivity(df)

    out_csv = OUT_DIR / "bandpass_sensitivity_summary.csv"
    summary.to_csv(out_csv, index=False)

    print(f"Saved: {out_csv}")
    print(summary.to_string(index=False))

    plot_measured_mode_sensitivity(summary)
    plot_etabs_mode_damping(summary)


if __name__ == "__main__":
    main()