from pathlib import Path

ETABS_MODES = {
    "ETABS_M1_UX_Strength": {
        "period_sec": 6.87,
        "direction": "UX",
        "description": "ETABS Mode 1 UX - Strength",
    },
    "ETABS_M2_RZ_Strength": {
        "period_sec": 5.95,
        "direction": "RZ",
        "description": "ETABS Mode 2 RZ - Strength",
    },
    "ETABS_M3_UY_Strength": {
        "period_sec": 5.49,
        "direction": "UY",
        "description": "ETABS Mode 3 UY - Strength",
    },
    "ETABS_M4_UX_Strength": {
        "period_sec": 2.71,
        "direction": "UX",
        "description": "ETABS Mode 4 UX - Strength",
    },
    "ETABS_M5_RZ_Strength": {
        "period_sec": 2.28,
        "direction": "RZ",
        "description": "ETABS Mode 5 RZ - Strength",
    },
    "ETABS_M6_UY_Strength": {
        "period_sec": 2.12,
        "direction": "UY",
        "description": "ETABS Mode 6 UY - Strength",
    },
    "ETABS_M1_UX_Service": {
        "period_sec": 6.18,
        "direction": "UX",
        "description": "ETABS Mode 1 UX - Service",
    },
    "ETABS_M2_RZ_Service": {
        "period_sec": 5.46,
        "direction": "RZ",
        "description": "ETABS Mode 2 RZ - Service",
    },
    "ETABS_M3_UY_Service": {
        "period_sec": 4.94,
        "direction": "RZ",
        "description": "ETABS Mode 3 UY - Service",
    },
    "ETABS_M4_UX_Service": {
        "period_sec": 2.43,
        "direction": "RZ",
        "description": "ETABS Mode 4 UX - Service",
    },
    "ETABS_M5_RZ_Service": {
        "period_sec": 2.10,
        "direction": "RZ",
        "description": "ETABS Mode 5 RZ - Service",
    },
    "ETABS_M6_UY_Service": {
        "period_sec": 1.91,
        "direction": "RZ",
        "description": "ETABS Mode 6 UY - Service",
    },
}


MEASURED_MODES = {
    "measured_2023_3p62s": {
        "dataset": "2023-03-01",
        "period_sec": 3.62,
        "frequency_hz": 1.0 / 3.62,
        "description": "Measured FDD dominant mode, 2023",
    },
    "measured_2025_3p01s": {
        "dataset": "2025-12-27",
        "period_sec": 3.01,
        "frequency_hz": 1.0 / 3.01,
        "description": "Measured FDD dominant mode, 2025",
    },
}


DATASETS = {
    "2023-03-01": {
        "accel_folder": Path("data/2023-03-01/Accelerometer"),
        "wind_folder": Path("data/2023-03-01/Wind Sensor"),
        "wind_file": Path("data/2023-03-01/Wind Sensor/08N4S-20230301_005350.txt"),
        "sync_groups": {
            "L25_3sync": ["29S2X", "29S2Y", "29S3X"],
            "L21_L25_6sync": ["21S2X", "21S2Y", "21S3X", "25S2X", "25S2Y", "25S3X"],
        },
    },
    "2025-12-27": {
        "accel_folder": Path("data/2025-12-27/Accelerometer"),
        "wind_folder": Path("data/2025-12-27/Wind Sensor"),
        "wind_file": Path("data/2025-12-27/Wind Sensor/31S4S-20251227_000722.txt"),
        "sync_groups": {
            "L25_3sync": ["29S2X", "29S2Y", "29S3X"],
            "L21_L25_6sync": ["21S2X", "21S2Y", "21S3X", "25S2X", "25S2Y", "25S3X"],
        },
    },
}

BANDPASS_SENSITIVITY = {
    "measured_2023_3p62s": [
        {
            "band_name": "narrow",
            "f_low": 0.25,
            "f_high": 0.31,
        },
        {
            "band_name": "medium",
            "f_low": 0.23,
            "f_high": 0.33,
        },
        {
            "band_name": "wide",
            "f_low": 0.20,
            "f_high": 0.36,
        },
    ],
    "measured_2025_3p01s": [
        {
            "band_name": "narrow",
            "f_low": 0.30,
            "f_high": 0.36,
        },
        {
            "band_name": "medium",
            "f_low": 0.28,
            "f_high": 0.38,
        },
        {
            "band_name": "wide",
            "f_low": 0.25,
            "f_high": 0.42,
        },
    ],
}

ETABS_BANDPASS_CASES = {
    "ETABS_M1_UX_Strength": [
        {"band_name": "narrow", "f_low": 0.135, "f_high": 0.156},
        {"band_name": "medium", "f_low": 0.127, "f_high": 0.164},
        {"band_name": "wide", "f_low": 0.116, "f_high": 0.175},
    ],
    "ETABS_M2_RZ_Strength": [
        {"band_name": "narrow", "f_low": 0.155, "f_high": 0.181},
        {"band_name": "medium", "f_low": 0.147, "f_high": 0.189},
        {"band_name": "wide", "f_low": 0.134, "f_high": 0.202},
    ],
    "ETABS_M3_UY_Strength": [
        {"band_name": "narrow", "f_low": 0.168, "f_high": 0.196},
        {"band_name": "medium", "f_low": 0.159, "f_high": 0.205},
        {"band_name": "wide", "f_low": 0.146, "f_high": 0.219},
    ],
    "ETABS_M4_UX_Strength": [
        {"band_name": "narrow", "f_low": 0.341, "f_high": 0.397},
        {"band_name": "medium", "f_low": 0.323, "f_high": 0.415},
        {"band_name": "wide", "f_low": 0.295, "f_high": 0.443},
    ],
    "ETABS_M5_RZ_Strength": [
        {"band_name": "narrow", "f_low": 0.406, "f_high": 0.471},
        {"band_name": "medium", "f_low": 0.384, "f_high": 0.493},
        {"band_name": "wide", "f_low": 0.351, "f_high": 0.526},
    ],
    "ETABS_M6_UY_Strength": [
        {"band_name": "narrow", "f_low": 0.436, "f_high": 0.507},
        {"band_name": "medium", "f_low": 0.413, "f_high": 0.531},
        {"band_name": "wide", "f_low": 0.377, "f_high": 0.566},
    ],

    "ETABS_M1_UX_Service": [
        {"band_name": "narrow", "f_low": 0.150, "f_high": 0.174},
        {"band_name": "medium", "f_low": 0.142, "f_high": 0.182},
        {"band_name": "wide", "f_low": 0.129, "f_high": 0.194},
    ],
    "ETABS_M2_RZ_Service": [
        {"band_name": "narrow", "f_low": 0.169, "f_high": 0.197},
        {"band_name": "medium", "f_low": 0.160, "f_high": 0.206},
        {"band_name": "wide", "f_low": 0.147, "f_high": 0.220},
    ],
    "ETABS_M3_UY_Service": [
        {"band_name": "narrow", "f_low": 0.187, "f_high": 0.218},
        {"band_name": "medium", "f_low": 0.177, "f_high": 0.228},
        {"band_name": "wide", "f_low": 0.162, "f_high": 0.243},
    ],
    "ETABS_M4_UX_Service": [
        {"band_name": "narrow", "f_low": 0.381, "f_high": 0.442},
        {"band_name": "medium", "f_low": 0.360, "f_high": 0.463},
        {"band_name": "wide", "f_low": 0.329, "f_high": 0.494},
    ],
    "ETABS_M5_RZ_Service": [
        {"band_name": "narrow", "f_low": 0.440, "f_high": 0.512},
        {"band_name": "medium", "f_low": 0.417, "f_high": 0.536},
        {"band_name": "wide", "f_low": 0.381, "f_high": 0.571},
    ],
    "ETABS_M6_UY_Service": [
        {"band_name": "narrow", "f_low": 0.484, "f_high": 0.563},
        {"band_name": "medium", "f_low": 0.458, "f_high": 0.589},
        {"band_name": "wide", "f_low": 0.419, "f_high": 0.628},
    ],
}