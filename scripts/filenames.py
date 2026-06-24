from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_sensor_file

RAW_DIR = Path("data/2025-12-27/Accelerometer")

FILES = [
    "21S2X-20251227_000254.txt",
    "21S2Y-20251227_000254.txt",
    "21S3X-20251227_000254.txt",
    "25S2X-20251227_000254.txt",
    "25S2Y-20251227_000254.txt",
    "25S3X-20251227_000254.txt",
    "29S2X-20251227_003323.txt",
    "29S2Y-20251227_003323.txt",
    "29S3X-20251227_003323.txt",
]

for file_name in FILES:
    meta, _ = read_sensor_file(RAW_DIR / file_name)

    print(
        meta["channel"],
        meta["Start_date"],
        meta["Start_time"]
    )