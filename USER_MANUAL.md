# User Manual

This manual explains, in plain language, **how to run this program** and **what
results (figures and tables) you can produce** with it. For the technical /
developer reference (module APIs, algorithm details), see [`Readme.md`](Readme.md).

---

## 1. What this program does

It takes raw sensor recordings from a tall building and tells you how the
building vibrates:

- **Modal frequencies / periods** — how fast the building naturally sways.
- **Damping ratios** — how quickly those sways die out.
- **Damping vs. wind** — how damping changes as the wind picks up.

The inputs are:

- **Accelerometer files** — vibration recorded at several floors (Levels 21, 25,
  and 29/Roof), in X, Y, and torsion directions.
- **Wind-sensor files** — wind speed measured at the same time.

You do not need to write any code to use it. You run the ready-made scripts in
the `scripts/` folder one at a time, and each one drops its figures and tables
into the `results/` folder.

---

## 2. Before you start (one-time setup)

1. **Install Python 3** and the required libraries:

   ```bash
   pip install numpy scipy pandas matplotlib
   ```

2. **Put your data in place.** Create a `data/` folder at the top of the project
   and arrange the raw files by date, like this:

   ```text
   data/
   ├─ 2023-03-01/
   │  ├─ Accelerometer/      <- accelerometer .txt files
   │  └─ Wind Sensor/        <- wind .txt file
   └─ 2025-12-27/
      ├─ Accelerometer/
      └─ Wind Sensor/
   ```

   The `data/` and `results/` folders are created automatically when needed and
   are **not** stored in the repository — they hold your own data and output.

3. **Run everything from the project's top folder** (the one that contains
   `src/`, `scripts/`, and `Readme.md`). For example:

   ```bash
   python scripts/plot_all_psd.py
   ```

> **Tip:** If your file names or dates differ from the examples, open the script
> and edit the file list / folder near the top (look for `FILES`, `RAW_DIR`, or
> `DATASETS`). Many scripts have a comment such as *"Change this path to your
> actual filename."*

---

## 3. Quick start

If you just want everything, run the scripts in this order. Each one builds on
the output of the previous ones.

```bash
python scripts/check_config.py              # 1. sanity-check your setup
python scripts/plot_all_psd.py              # 2. frequency content
python scripts/plot_all_fdd.py              # 3. identify building modes
python scripts/extract_fdd_peaks.py         # 4. table of modal frequencies
python scripts/apply_bandpass_matrix.py     # 5. isolate one mode at a time
python scripts/estimate_damping_rdt.py      # 6. estimate damping
python scripts/analyze_bandpass_sensitivity.py  # 7. check damping robustness
python scripts/summarize_wind.py            # 8. summarize wind speed
python scripts/estimate_windowed_damping.py # 9. damping over time
python scripts/analyze_wind_damping_trend.py    # 10. damping vs. wind
```

Look in the `results/` folder after each step to see what was produced.

---

## 4. The workflow, step by step

The program is organized as a pipeline. You can run the whole thing, or stop at
whatever answer you need.

### Step 0 — Check your setup
**Script:** `check_config.py`
Confirms that the configuration is consistent and that the data files it expects
actually exist. Run this first to catch missing files before a long analysis.
*Produces:* messages in the terminal only.

### Step 1 — Look at the frequency content (PSD)
**Scripts:** `plot_all_psd.py`, `plot_all_displacement_psd.py`
Shows which frequencies have the most energy — the first clue to where the
building's modes are. The "displacement" version emphasizes the slow, tall-building
sway modes.

### Step 2 — Identify the building modes (FDD)
**Scripts:** `plot_fdd.py`, `plot_all_fdd.py`, `extract_fdd_peaks.py`
Combines several synchronized sensors to pick out the building's true shared
motion and locate each mode. `extract_fdd_peaks.py` turns those peaks into a
table you can read.

### Step 3 — Isolate one mode (bandpass filtering)
**Scripts:** `apply_bandpass_modes.py`, `apply_bandpass_matrix.py`
Filters the signal down to a single mode so its decay can be measured cleanly.
`apply_bandpass_matrix.py` runs many cases at once (different modes and filter
widths) and saves the filtered signals for the next step.

### Step 4 — Estimate damping (RDT)
**Script:** `estimate_damping_rdt.py`
Uses the Random Decrement Technique to turn the filtered vibration into a
free-decay curve, then fits how fast it decays to get the **damping ratio**.
This is the program's main result.

### Step 5 — Check how trustworthy the damping is
**Script:** `analyze_bandpass_sensitivity.py`
Shows how much the damping estimate changes when you use narrow, medium, or wide
filters — a way to judge confidence in the number.

### Step 6 — Wind, and damping vs. wind
**Scripts:** `summarize_wind.py`, `estimate_windowed_damping.py`,
`analyze_wind_damping_trend.py`
Summarizes the wind record, estimates damping in rolling 30-minute windows, and
plots how damping trends with wind speed.

### Utility / spot-check scripts
- `filenames.py` — prints the channel, date, and start time stored inside a set
  of raw files (handy for checking what you have).
- `test_read_wind.py` — reads a wind file and plots a quick sample to confirm it
  loads correctly.

---

## 5. What you can produce (outputs)

Everything is written into the `results/` folder. Figures are `.png` images;
tables are `.csv` files you can open in Excel.

### Figures (`.png`)

| Output | Produced by | What it shows |
| --- | --- | --- |
| `psd_x_direction.png`, `psd_y_direction.png`, `psd_torsion_channels.png` | `plot_all_psd.py` | Frequency content per direction |
| `disp_psd_x_direction.png`, `disp_psd_y_direction.png`, `disp_psd_torsion_channels.png` | `plot_all_displacement_psd.py` | Same, emphasizing slow sway modes |
| `fdd_*.png`, `fdd_comparison_first_singular_value.png`, `fdd_all_9_sensors.png` | `plot_fdd.py`, `plot_all_fdd.py` | Identified building modes (FDD) |
| `results/bandpass_matrix/psd_*.png` | `apply_bandpass_matrix.py` | Before/after a mode is isolated |
| `results/bandpass/psd_before_after_*.png`, `time_preview_*.png` | `apply_bandpass_modes.py` | Filter check plots |
| `results/rdt/rdt_decay_*.png` | `estimate_damping_rdt.py` | The decay curve fitted for damping |
| `results/rdt/rdt_triggers_*.png` | `estimate_damping_rdt.py` | Where decay traces were picked |
| `results/sensitivity/bandpass_sensitivity_*.png`, `etabs_mode_damping_*.png` | `analyze_bandpass_sensitivity.py` | Damping vs. filter width |
| `results/wind/wind_summary_10m_mph_*.png` | `summarize_wind.py` | Wind-speed summary |
| `results/wind_sample.png` | `test_read_wind.py` | Quick wind-file preview |
| `results/windowed_damping/damping_vs_mean_wind_speed_mph.png`, `damping_time_history_*.png` | `estimate_windowed_damping.py` | Damping over time and vs. wind |
| `results/windowed_damping/binned_damping_vs_wind_mph.png`, `low_wind_damping_fit_mph.png` | `analyze_wind_damping_trend.py` | Damping trend binned by wind |

### Tables (`.csv`)

| Output | Produced by | What it contains |
| --- | --- | --- |
| `results/fdd_peak_summary.csv` | `extract_fdd_peaks.py` | Measured modal frequencies/periods vs. reference |
| `results/rdt/damping_summary.csv` | `estimate_damping_rdt.py` | Damping estimate and fit quality per channel/case |
| `results/sensitivity/bandpass_sensitivity_summary.csv` | `analyze_bandpass_sensitivity.py` | How damping varies with filter width |
| `results/wind/wind_summary_*.csv`, `wind_summary_all.csv` | `summarize_wind.py` | Windowed wind statistics |
| `results/windowed_damping/windowed_damping_summary.csv` | `estimate_windowed_damping.py` | Damping per 30-min window joined with wind |
| `results/windowed_damping/binned_damping_*.csv`, `low_wind_intercept_fit.csv` | `analyze_wind_damping_trend.py` | Damping binned by wind, and low-wind fit |

### Intermediate data (`.npz`)

`apply_bandpass_modes.py` and `apply_bandpass_matrix.py` also save the filtered
signals into `data/processed/` and `data/processed_matrix/`. You don't open these
directly — the damping scripts read them automatically.

---

## 6. Common questions

**"I only care about the building's frequencies."**
Run Step 0 → Step 1 → Step 2, then open `results/fdd_peak_summary.csv`.

**"I want a single damping number."**
Run through Step 4, then open `results/rdt/damping_summary.csv`. Higher
`fit_r_squared` (closer to 1.0) means a more reliable estimate.

**"I want to see how damping depends on wind."**
Run the full pipeline, then look at the figures in
`results/windowed_damping/`.

**A script fails saying a file is missing.**
Open the script and update the file names / folder near the top to match your
own data, then run `check_config.py` again.

---

## 7. Where to learn more

- [`Readme.md`](Readme.md) — full technical reference: data formats, sensor
  strategy, the library modules in `src/`, the algorithms, and the reference
  modes used for comparison.
- `notebooks/` — exploratory Jupyter notebooks for experimenting with the data.
