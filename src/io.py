from pathlib import Path
import pandas as pd


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
                metadata["channel"] = parts[1].replace(",", "")
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