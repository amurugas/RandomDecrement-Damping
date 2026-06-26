from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

from src.wind import correct_to_reference_height, mps_to_mph

def read_sensor_metadata(path):
    path = Path(path)
    metadata = {}

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            parts = line.strip().split()

            if not parts:
                continue

            if parts[0].startswith("Time"):
                metadata["data_start_line"] = i

                channel_unit = parts[1]
                if "," in channel_unit:
                    channel, unit = channel_unit.split(",", 1)
                else:
                    channel, unit = channel_unit, ""

                metadata["channel"] = channel
                metadata["unit"] = unit
                break

            if len(parts) >= 2:
                metadata[parts[0]] = " ".join(parts[1:])

    metadata["sampling_rate_hz"] = float(metadata["Sampling_rate"])
    return metadata


def read_sensor_file(path):
    path = Path(path)
    meta = read_sensor_metadata(path)

    df = pd.read_csv(
        path,
        sep=r"\s+",
        skiprows=meta["data_start_line"] + 1,
        names=["time_sec", "accel_cm_s2"],
        engine="c",
    )

    df["accel_m_s2"] = df["accel_cm_s2"] / 100.0

    return meta, df

def read_sensor_sample(path, nrows=100_000):
    path = Path(path)
    meta = read_sensor_metadata(path)

    df = pd.read_csv(
        path,
        sep=r"\s+",
        skiprows=meta["data_start_line"] + 1,
        names=["time_sec", "accel_cm_s2"],
        nrows=nrows,
        engine="c",
    )

    df["accel_m_s2"] = df["accel_cm_s2"] / 100.0

    return meta, df




def parse_start_datetime(meta):
    """
    Parse Start_date and Start_time from sensor metadata.

    Expected:
        Start_date = DD.MM.YYYY
        Start_time = HH:MM:SS.sss
    """
    date_str = meta["Start_date"]
    time_str = meta["Start_time"]

    return datetime.strptime(
        f"{date_str} {time_str}",
        "%d.%m.%Y %H:%M:%S.%f"
    )


def read_wind_file(path, nrows=None):
    """
    Read wind speed file.

    Expected header:
        Time:sec   08N4S,m/s

    Wind-speed unit conversion (m/s -> mph) and reference-height
    correction are applied here, at the single point the raw wind record
    is consumed, using ``src.wind``. Downstream code consumes the
    resulting columns and must not re-derive them.

    Returns
    -------
    meta : dict
    df : DataFrame with:
        time_sec
        wind_m_s          raw anemometer speed [m/s]
        wind_ref_m_s      speed corrected to the reference height [m/s]
        wind_ref_mph      reference-height speed [mph]
        timestamp
    """
    path = Path(path)
    meta = read_sensor_metadata(path)

    df = pd.read_csv(
        path,
        sep=r"\s+",
        skiprows=meta["data_start_line"] + 1,
        names=["time_sec", "wind_m_s"],
        nrows=nrows,
        engine="python",
    )

    df["wind_ref_m_s"] = correct_to_reference_height(df["wind_m_s"])
    df["wind_ref_mph"] = mps_to_mph(df["wind_ref_m_s"])

    start_dt = parse_start_datetime(meta)

    df["timestamp"] = [
        start_dt + timedelta(seconds=float(t))
        for t in df["time_sec"].to_numpy()
    ]

    return meta, df