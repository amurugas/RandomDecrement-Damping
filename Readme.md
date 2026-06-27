# Random Decrement Damping Estimation

This repository estimates building modal frequencies and damping ratios from
ambient vibration data recorded by accelerometers distributed through the height
of a building. The source data consists of multi-day acceleration records, plus a
co-located wind sensor used to relate damping to wind excitation.

The workflow is output-only (operational) modal identification under wind
excitation. It uses Power Spectral Density (PSD), Cross-Spectral Density (CSD),
and Frequency Domain Decomposition (FDD) to identify modal frequencies, then the
Random Decrement Technique (RDT) with Hilbert-envelope exponential-decay fitting
to estimate damping ratios. Damping is also tracked over time and correlated with
measured wind speed.

## Repository layout

```text
src/        Reusable library code (I/O, filtering, spectral/FDD, RDT, damping, config)
scripts/    Runnable analysis scripts that form the pipeline
notebooks/  Exploratory Jupyter notebooks
```

Scripts are intended to be run from the repository root (each script appends the
repo root to `sys.path` so that `from src... import ...` works). All scripts read
from `data/` and write figures and CSV summaries into `results/`. Both
directories are created on demand and are not tracked in the repository.

## Data

### Accelerometers

Raw accelerometer files are stored by date:

```text
data/
├─ 2023-03-01/
│  ├─ Accelerometer/
│  └─ Wind Sensor/
└─ 2025-12-27/
   ├─ Accelerometer/
   └─ Wind Sensor/
```

Each accelerometer text file contains metadata followed by two columns:

```text
Station_code    GMS05
Sampling_rate   100.0000
Start_date      DD.MM.YYYY
Start_time      HH:MM:SS.sss
Time:sec        21S2X,cm/s2
```

Acceleration is read in `cm/s²` and converted to `m/s²`. Channel names encode the
level and component, e.g. `21S2X` is Level 21, sensor 2, X component.

### Wind sensor

Each dataset also includes a wind-speed record with the same metadata layout and a
`Time:sec  <channel>,m/s` data header. Wind speed is read in `m/s`. All wind-speed
unit conversion and the optional reference-height correction are centralized in
`src/wind.py` and applied **once**, where the raw record is consumed in
`src.io.read_wind_file`. Downstream scripts read the resulting columns rather than
re-deriving the conversion or profile.

`read_wind_file` returns a DataFrame with:

| Column | Meaning |
| --- | --- |
| `wind_m_s` | Raw measured wind speed at the anemometer height (m/s). |
| `wind_ref_m_s` | Wind speed corrected to the reference height (m/s); identical to `wind_m_s` until the heights are configured. |
| `wind_ref_mph` | Reference-height wind speed converted to mph. |
| `timestamp` | Absolute time of each sample, from the file's start date/time. |

#### Reference-height correction

`src/wind.py` exposes the exact `MPH_PER_MPS` factor plus a power-law (e.g. ASCE
Exposure C) wind-profile correction:

```text
V_ref = V_meas * (REFERENCE_HEIGHT_M / ANEMOMETER_HEIGHT_M) ** WIND_PROFILE_EXPONENT
```

`ANEMOMETER_HEIGHT_M` and `REFERENCE_HEIGHT_M` default to `None`, so the correction
is the identity (factor `1.0`) and existing results are unchanged. Setting both
heights in `src/wind.py` activates the correction everywhere the centralized
helpers (`mps_to_mph`, `correct_to_reference_height`, `height_correction_factor`)
are used — no other file needs to change.

## Sensor strategy

Sensors are located at Levels 21, 25, and 29/Roof. The Level 29 sensors start
about 30 minutes later than the Level 21 and Level 25 sensors. Because CSD/FDD
requires synchronized channels, sensors are grouped by common start time rather
than mixed across the offset. The synchronized groups in use are:

```text
6 sensors (L21 + L25, common start): 21S2X, 21S2Y, 21S3X, 25S2X, 25S2Y, 25S3X
3 sensors (L29/Roof, later common start): 29S2X, 29S2Y, 29S3X
```

These groups are defined per dataset in `DATASETS[...]["sync_groups"]`
(`L21_L25_6sync` and `L29_roof_3sync`) in `src/config.py`; the historical
`L25_3sync` alias remains for compatibility. `scripts/plot_all_fdd.py` now uses
those config groups and includes explicit time-aligned nine-channel FDD cases.

## Library modules (`src/`)

| Module | Purpose |
| --- | --- |
| `io.py` | Read accelerometer and wind files. `read_sensor_metadata`, `read_sensor_file` (returns `meta`, `DataFrame` with `time_sec`, `accel_cm_s2`, `accel_m_s2`), `read_sensor_sample`, `parse_start_datetime`, and `read_wind_file` (returns `time_sec`, `wind_m_s`, `wind_ref_m_s`, `wind_ref_mph`, `timestamp`). |
| `wind.py` | Centralized wind-speed handling: the exact `MPH_PER_MPS` factor, `mps_to_mph`, and the power-law reference-height correction (`height_correction_factor`, `correct_to_reference_height`). Conversion and height profile are defined once and applied once, in `io.read_wind_file`. |
| `filtering.py` | `bandpass_filter` — zero-phase Butterworth bandpass (`sosfiltfilt`) to isolate a single mode. |
| `fdd.py` | `build_csd_matrix` builds the cross-spectral density matrix `G(f)` via Welch CSD; `compute_fdd` runs an SVD at each frequency line to return singular values and mode shapes. |
| `rdt.py` | `random_decrement_signature` — Random Decrement Signature from positive level upcrossings, producing a free-decay-like signal. Pass `return_segments=True` to also get the individual averaged traces and their trigger sample indices. |
| `damping.py` | `fit_exponential_decay` — Hilbert envelope plus exponential fit to estimate the damping ratio (`zeta = alpha / omega_n`) with an R² goodness-of-fit. |
| `config.py` | Central configuration: `DATASETS`, ETABS reference modes (`ETABS_MODES`), measured modes (`MEASURED_MODES`), and bandpass case tables (`BANDPASS_SENSITIVITY`, `ETABS_BANDPASS_CASES`). |

`preprocessing.py` and `spectral.py` are placeholders reserved for future use.

## Pipeline (`scripts/`)

The scripts roughly follow the analysis order below.

### 1. Inspection and I/O checks

| Script | Description |
| --- | --- |
| `filenames.py` | Print channel/start-date/start-time metadata for a set of raw files. |
| `test_read_wind.py` | Read and plot a sample of a wind file as a sanity check. |
| `check_config.py` | Validate `src/config.py`: confirm bandpass entries exist for each mode and that referenced channel files are present. |

### 2. Single-channel PSD

| Script | Description |
| --- | --- |
| `plot_all_psd.py` | Acceleration PSD (Welch) for all channels — general frequency content. |
| `plot_all_displacement_psd.py` | Displacement-like PSD, computed by dividing acceleration PSD by `(2πf)^4` to emphasize long-period building modes. |

### 3. Cross-Spectral Density and FDD

For synchronized sensors the CSD matrix is built at each frequency, then SVD is
applied:

```text
G(f) = U Σ Uᴴ
```

The first singular value identifies the dominant coherent building motion at each
frequency.

| Script | Description |
| --- | --- |
| `plot_fdd.py` | FDD for a single hard-coded case. |
| `plot_all_fdd.py` | FDD for all synchronized `CASES` (2023/2025, 6-sync and 3-sync); also defines the shared `CASES` and `ETABS_MODES` reused downstream. |
| `extract_fdd_peaks.py` | Peak-pick the first singular value into a table of measured modal frequencies/periods, compared against ETABS modes. Writes `results/fdd_peak_summary.csv`. |

### 4. Bandpass isolation of a mode

| Script | Description |
| --- | --- |
| `apply_bandpass_modes.py` | Bandpass selected channels around a chosen measured modal frequency (hard-coded `MODAL_CASES`); writes filtered series to `data/processed/` and check plots to `results/bandpass/`. |
| `apply_bandpass_matrix.py` | Run a full matrix of bandpass cases driven by `config.py` (`MEASURED_MODES`, `ETABS_MODES`, `BANDPASS_SENSITIVITY`, `ETABS_BANDPASS_CASES`); writes to `data/processed_matrix/` and `results/bandpass_matrix/`. |

### 5. Damping estimation (RDT)

| Script | Description |
| --- | --- |
| `estimate_damping_rdt.py` | Downsample the bandpassed series, compute the Random Decrement Signature, fit an exponential decay envelope, and record damping. Reads `data/processed_matrix/` and writes `results/rdt/damping_summary.csv`. For each channel it saves an RDT decay plot (`rdt_decay_*.png`) that overlays the individual averaged traces in half-transparent colors behind the signature, plus a time-history plot (`rdt_triggers_*.png`) marking the threshold-crossing points where traces are picked. |
| `analyze_bandpass_sensitivity.py` | Summarize how the damping estimate varies across narrow/medium/wide bandpass widths. Reads `results/rdt/damping_summary.csv`; writes to `results/sensitivity/`. |

### 6. Wind, and damping vs. wind trend

| Script | Description |
| --- | --- |
| `summarize_wind.py` | Resample wind records into windowed mean/max statistics. Writes `results/wind/wind_summary_all.csv`. |
| `estimate_windowed_damping.py` | Estimate damping in rolling 30-minute windows and join with wind statistics. Writes `results/windowed_damping/windowed_damping_summary.csv`. |
| `analyze_wind_damping_trend.py` | Bin windowed damping by wind speed and plot the damping-vs-wind trend. |

## Reference modes (`config.py`)

Measured peaks are compared against ETABS modal periods (Strength and Service
variants are both defined in `config.py`). The Strength modes are:

```text
Mode 1 UX: 6.87 sec, 0.146 Hz
Mode 2 RZ: 5.95 sec, 0.168 Hz
Mode 3 UY: 5.49 sec, 0.182 Hz
Mode 4 UX: 2.71 sec, 0.370 Hz
Mode 5 RZ: 2.28 sec, 0.438 Hz
Mode 6 UY: 2.12 sec, 0.472 Hz
```

The dominant coherent measured modes used for bandpass/RDT are:

```text
2023 data: T ≈ 3.62 sec (≈ 0.28 Hz)
2025 data: T ≈ 3.01 sec (≈ 0.33 Hz)
```

## Typical run order

```text
python scripts/check_config.py
python scripts/plot_all_psd.py
python scripts/plot_all_fdd.py
python scripts/extract_fdd_peaks.py
python scripts/apply_bandpass_matrix.py
python scripts/estimate_damping_rdt.py
python scripts/analyze_bandpass_sensitivity.py
python scripts/summarize_wind.py
python scripts/estimate_windowed_damping.py
python scripts/analyze_wind_damping_trend.py
```

## Dependencies

The code targets Python 3 and relies on `numpy`, `scipy`, `pandas`, and
`matplotlib`.

## Next steps

1. Confirm the dominant measured mode for each dataset from `results/fdd_peak_summary.csv`.
2. Tighten bandpass widths using the sensitivity results.
3. Validate damping estimates across channels and dates.
4. Review the time-aligned 9-channel FDD output against the separate sync-group
   FDD results.
