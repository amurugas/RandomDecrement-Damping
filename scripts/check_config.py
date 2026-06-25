from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import (
    DATASETS,
    ETABS_MODES,
    ETABS_BANDPASS_CASES,
    MEASURED_MODES,
    BANDPASS_SENSITIVITY,
)


def check_file_exists(folder, channel):
    matches = sorted(folder.glob(f"{channel}-*.txt"))
    return matches


def main():
    print("\nChecking ETABS mode configuration...")

    missing_etabs_bands = set(ETABS_MODES.keys()) - set(ETABS_BANDPASS_CASES.keys())
    extra_etabs_bands = set(ETABS_BANDPASS_CASES.keys()) - set(ETABS_MODES.keys())

    if missing_etabs_bands:
        print("Missing ETABS bandpass entries:")
        for x in sorted(missing_etabs_bands):
            print("  ", x)

    if extra_etabs_bands:
        print("Extra ETABS bandpass entries:")
        for x in sorted(extra_etabs_bands):
            print("  ", x)

    if not missing_etabs_bands and not extra_etabs_bands:
        print("ETABS mode keys match bandpass keys.")

    print("\nChecking measured mode configuration...")

    missing_measured_bands = set(MEASURED_MODES.keys()) - set(BANDPASS_SENSITIVITY.keys())

    if missing_measured_bands:
        print("Missing measured-mode bandpass entries:")
        for x in sorted(missing_measured_bands):
            print("  ", x)
    else:
        print("Measured mode keys match bandpass sensitivity keys.")

    print("\nChecking datasets and files...")

    total_accel_files = 0

    for dataset, info in DATASETS.items():
        accel_folder = info["accel_folder"]
        wind_file = info.get("wind_file")

        print(f"\nDataset: {dataset}")
        print(f"  Accel folder: {accel_folder}")
        print(f"  Accel folder exists: {accel_folder.exists()}")

        if wind_file is not None:
            print(f"  Wind file: {wind_file}")
            print(f"  Wind file exists: {wind_file.exists()}")

        for group_name, channels in info["sync_groups"].items():
            print(f"\n  Group: {group_name}")

            for channel in channels:
                matches = check_file_exists(accel_folder, channel)

                if matches:
                    print(f"    {channel}: {matches[0].name}")
                    total_accel_files += 1
                else:
                    print(f"    MISSING: {channel}")

    n_etabs_modes = len(ETABS_MODES)
    n_etabs_bands = sum(len(v) for v in ETABS_BANDPASS_CASES.values())
    n_measured_bands = sum(len(v) for v in BANDPASS_SENSITIVITY.values())

    print("\nRun size estimate:")
    print(f"  ETABS modes: {n_etabs_modes}")
    print(f"  ETABS band cases total: {n_etabs_bands}")
    print(f"  Measured band sensitivity cases total: {n_measured_bands}")
    print(f"  Available channel-file references checked: {total_accel_files}")

    print("\nConfig check complete.")


if __name__ == "__main__":
    main()