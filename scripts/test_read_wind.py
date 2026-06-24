from pathlib import Path
import sys

import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io import read_wind_file


file_path = Path("data/2023-03-01/Wind Sensor/08N4S-20230301_005350.txt")
# Change this path to your actual wind filename.

meta, df = read_wind_file(file_path, nrows=100_000)

print(meta)
print(df.head())
print(df.tail())

plt.figure(figsize=(12, 4))
plt.plot(df["timestamp"], df["wind_m_s"])
plt.xlabel("Time")
plt.ylabel("Wind speed [m/s]")
plt.title(f"Wind speed sample - {meta['channel']}")
plt.grid(True)
plt.tight_layout()

out = Path("results/wind_sample.png")
out.parent.mkdir(exist_ok=True)
plt.savefig(out, dpi=300)
plt.close()

print(f"Saved: {out}")