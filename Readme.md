# Random Decrement Damping Estimation

This repository estimates building modal frequencies and damping ratios from ambient vibration data recorded by accelerometers in a building. The source data consists of multi-day acceleration records from sensors distributed through the building height. The current workflow focuses on output-only modal identification under wind excitation, using Power Spectral Density (PSD), Cross-Spectral Density (CSD), Frequency Domain Decomposition (FDD), and later Random Decrement Technique (RDT) or Natural Excitation Technique (NeXT) for damping estimation.

## Data

Raw accelerometer files are stored by date:

```text
data/
├─ 2023-03-01/
│  └─ Accelerometer/
└─ 2025-12-27/
   └─ Accelerometer/
```

Each text file contains metadata followed by two columns:

```text
Station_code    GMS05
Sampling_rate   100.0000
Start_date      DD.MM.YYYY
Start_time      HH:MM:SS.sss
Time:sec        21S2X,cm/s2
```

Acceleration is read in `cm/s²` and converted to `m/s²`.

## Current Sensor Strategy

The available sensors are located at Levels 21, 25, and 29/Roof. The Level 29 sensors start about 30 minutes later than the Level 21 and Level 25 sensors, so they are not currently included in CSD/FDD calculations. CSD requires synchronized channels.

Current valid synchronized cases:

```text
2023-03-01 | 6 sensors | 21S2X, 21S2Y, 21S3X, 25S2X, 25S2Y, 25S3X
2023-03-01 | 3 sensors | 25S2X, 25S2Y, 25S3X
2025-12-27 | 6 sensors | 21S2X, 21S2Y, 21S3X, 25S2X, 25S2Y, 25S3X
2025-12-27 | 3 sensors | 25S2X, 25S2Y, 25S3X
```

Roof sensors can be added later after explicit time alignment.

## Workflow

### 1. Read and clean sensor data

`src/io.py` parses metadata and acceleration records from the raw text files.

Main output:

```text
time_sec
accel_cm_s2
accel_m_s2
```

### 2. Single-channel PSD

PSD is used for initial inspection of measured vibration energy.

Scripts:

```text
scripts/plot_all_psd.py
scripts/plot_all_displacement_psd.py
```

Acceleration PSD is useful for general frequency content. Displacement-like PSD is computed by dividing acceleration PSD by `(2πf)^4`, which emphasizes long-period building modes.

### 3. Cross-Spectral Density and FDD

For synchronized sensors, the CSD matrix is built at each frequency:

```text
G(f) = cross-spectral density matrix
```

Then Singular Value Decomposition is applied:

```text
G(f) = U Σ Uᴴ
```

The first singular value identifies the dominant coherent building motion at each frequency.

Scripts:

```text
scripts/plot_fdd_cases.py
```

Outputs:

```text
results/fdd_2023_6sync_L21_L25.png
results/fdd_2023_3sync_L25.png
results/fdd_2025_6sync_L21_L25.png
results/fdd_2025_3sync_L25.png
results/fdd_comparison_first_singular_value.png
```

### 4. Peak extraction

FDD peak extraction converts visual observations into a table of measured modal frequencies and periods.

Script:

```text
scripts/extract_fdd_peaks.py
```

Output:

```text
results/fdd_peak_summary.csv
```

This table compares measured FDD peaks against ETABS modal frequencies.

## ETABS Reference Modes

The measured peaks are compared against ETABS modal periods:

```text
Mode 1 UX: 6.87 sec, 0.146 Hz
Mode 2 RZ: 5.95 sec, 0.168 Hz
Mode 3 UY: 5.49 sec, 0.182 Hz
Mode 4 UX: 2.71 sec, 0.370 Hz
Mode 5 RZ: 2.28 sec, 0.438 Hz
Mode 6 UY: 2.12 sec, 0.472 Hz
```

Initial FDD results suggest dominant coherent measured response near:

```text
2023 data: approximately 0.28 Hz, T ≈ 3.6 sec
2025 data: approximately 0.32–0.33 Hz, T ≈ 3.0–3.1 sec
```

These should be confirmed using `fdd_peak_summary.csv`.

## Next Steps

1. Review `results/fdd_peak_summary.csv`.
2. Select the dominant measured mode for each dataset.
3. Bandpass the acceleration response around that measured modal frequency.
4. Use RDT or NeXT to extract an impulse-response-like free decay.
5. Use the Hilbert envelope and exponential decay fitting to estimate damping ratio.
6. Validate damping estimates across channels and dates.
7. Later, time-align roof sensors and repeat FDD with all 9 channels.
