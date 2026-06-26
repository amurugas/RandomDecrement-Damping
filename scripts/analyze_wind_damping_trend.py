from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.wind import mps_to_mph


INPUT_CSV = Path("results/windowed_damping/windowed_damping_summary.csv")
OUT_DIR = Path("results/windowed_damping")
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIND_BINS = [0, 5, 10, 15, 20, 25, 30, 35, 45]

def load_data():
    df = pd.read_csv(INPUT_CSV)

    df["window_start"] = pd.to_datetime(df["window_start"])
    df["window_end"] = pd.to_datetime(df["window_end"])

    # Basic quality filter
    df = df[
        (df["quality_flag"] == True)
        & np.isfinite(df["damping_percent"])
        & np.isfinite(df["wind_mean_m_s"])
        & (df["damping_percent"] > 0)
        & (df["damping_percent"] < 15)
        & (df["fit_r_squared"] >= 0.70)
        & (df["n_segments"] >= 100)
    ].copy()

    if "wind_mean_mph" not in df.columns:
        df["wind_mean_mph"] = mps_to_mph(df["wind_mean_m_s"])

    return df


def make_binned_summary(df):
    df["wind_bin_mph"] = pd.cut(
        df["wind_mean_mph"],
        bins=WIND_BINS,
        right=False,
        include_lowest=True,
    )

    summary = (
        df.groupby(["dataset", "channel", "wind_bin_mph"], observed=True)
        .agg(
            n_windows=("damping_percent", "count"),
            wind_mean_mph=("wind_mean_mph", "mean"),
            wind_mean_m_s=("wind_mean_m_s", "mean"),
            damping_median_percent=("damping_percent", "median"),
            damping_mean_percent=("damping_percent", "mean"),
            damping_p25_percent=("damping_percent", lambda x: np.percentile(x, 25)),
            damping_p75_percent=("damping_percent", lambda x: np.percentile(x, 75)),
        )
        .reset_index()
    )

    return summary

def make_overall_binned_summary(df):
    df["wind_bin_mph"] = pd.cut(
        df["wind_mean_mph"],
        bins=WIND_BINS,
        right=False,
        include_lowest=True,
    )

    summary = (
        df.groupby(["wind_bin_mph"], observed=True)
        .agg(
            n_windows=("damping_percent", "count"),
            wind_mean_mph=("wind_mean_mph", "mean"),
            wind_mean_m_s=("wind_mean_m_s", "mean"),
            damping_median_percent=("damping_percent", "median"),
            damping_mean_percent=("damping_percent", "mean"),
            damping_p25_percent=("damping_percent", lambda x: np.percentile(x, 25)),
            damping_p75_percent=("damping_percent", lambda x: np.percentile(x, 75)),
        )
        .reset_index()
    )

    return summary


def fit_low_wind_intercept(df, max_wind_mph=9.0):
    """
    Fit damping = a + b * wind_mean_mph using low-wind windows.

    The intercept a is a crude low-wind proxy for baseline damping.
    """
    low = df[df["wind_mean_mph"] <= max_wind_mph].copy()

    if len(low) < 5:
        return None

    x = low["wind_mean_mph"].to_numpy()
    y = low["damping_percent"].to_numpy()

    b, a = np.polyfit(x, y, deg=1)

    return {
        "max_wind_used_mph": max_wind_mph,
        "n_windows": len(low),
        "intercept_percent": a,
        "slope_percent_per_mph": b,
    }


def plot_binned_trend(overall):
    plt.figure(figsize=(10, 6))

    x = overall["wind_mean_mph"]
    y = overall["damping_median_percent"]
    yerr_lower = y - overall["damping_p25_percent"]
    yerr_upper = overall["damping_p75_percent"] - y

    plt.errorbar(
        x,
        y,
        yerr=[yerr_lower, yerr_upper],
        fmt="o-",
        capsize=4,
        label="Median damping with IQR",
    )

    plt.xlabel("Mean wind speed [mph]")
    plt.ylabel("RDT damping estimate [%]")
    plt.title("Binned damping trend vs mean wind speed")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()

    out_path = OUT_DIR / "binned_damping_vs_wind_mph.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def plot_low_wind_fit(df, fit):
    plt.figure(figsize=(10, 6))

    plt.scatter(
        df["wind_mean_mph"],
        df["damping_percent"],
        alpha=0.35,
        label="Window estimates",
    )

    if fit is not None:
        x_line = np.linspace(0, df["wind_mean_mph"].max(), 100)
        y_line = fit["intercept_percent"] + fit["slope_percent_per_mph"] * x_line

        plt.plot(
            x_line,
            y_line,
            linewidth=2,
            label=(
                f"Low-wind fit: ζ = {fit['intercept_percent']:.2f}% "
                f"+ {fit['slope_percent_per_mph']:.3f}%/mph · U"
            ),
        )

    plt.xlabel("Mean wind speed [mph]")
    plt.ylabel("RDT damping estimate [%]")
    plt.title("Low-wind damping trend fit")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()

    out_path = OUT_DIR / "low_wind_damping_fit_mph.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def main():
    df = load_data()

    print(f"Good-quality windows: {len(df)}")

    by_channel = make_binned_summary(df)
    overall = make_overall_binned_summary(df)

    by_channel_csv = OUT_DIR / "binned_damping_by_channel.csv"
    overall_csv = OUT_DIR / "binned_damping_overall.csv"

    by_channel.to_csv(by_channel_csv, index=False)
    overall.to_csv(overall_csv, index=False)

    print(f"Saved: {by_channel_csv}")
    print(f"Saved: {overall_csv}")

    fit = fit_low_wind_intercept(df, max_wind_mph=9.0)

    if fit is not None:
        fit_csv = OUT_DIR / "low_wind_intercept_fit.csv"
        pd.DataFrame([fit]).to_csv(fit_csv, index=False)

        print("\nLow-wind fit:")
        print(f"  windows used: {fit['n_windows']}")
        print(f"  intercept: {fit['intercept_percent']:.2f}%")
        print(f"  slope: {fit['slope_percent_per_mph']:.3f}% per mph")
        print(f"Saved: {fit_csv}")

    print("\nOverall binned summary:")
    print(overall.to_string(index=False))

    plot_binned_trend(overall)
    plot_low_wind_fit(df, fit)


if __name__ == "__main__":
    main()