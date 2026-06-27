"""Centralized wind-speed handling.

Single home for wind-speed unit conversion (m/s -> mph) and the optional
reference-height correction. These were previously duplicated across several
scripts and re-derived at multiple pipeline stages. Import from here so the
conversion factor and the height profile are defined exactly once and applied
once, where the raw wind record is consumed (see ``src.io.read_wind_file``).
"""

# Exact m/s -> mph conversion factor.
MPH_PER_MPS = 2.2369362920544

# --- Reference-height correction parameters -------------------------------
#
# A power-law (e.g. ASCE Exposure C) wind profile is used to translate a wind
# speed measured at the anemometer height to the equivalent speed at a chosen
# reference height:
#
#     V_ref = V_meas * (REFERENCE_HEIGHT_M / ANEMOMETER_HEIGHT_M) ** exponent
#
# The site geometry (anemometer and reference heights) is not documented in the
# repository, so both heights default to ``None``. While either is unset the
# correction is the identity (factor 1.0), which avoids silently changing
# existing results. Setting both heights below activates the correction
# everywhere the centralized helpers are used -- no other file needs to change.
ANEMOMETER_HEIGHT_M = None
REFERENCE_HEIGHT_M = None
WIND_PROFILE_EXPONENT = 0.14


def mps_to_mph(speed_m_s):
    """Convert a wind speed (or array of speeds) from m/s to mph."""
    return speed_m_s * MPH_PER_MPS


def height_correction_factor(
    anemometer_height_m=ANEMOMETER_HEIGHT_M,
    reference_height_m=REFERENCE_HEIGHT_M,
    exponent=WIND_PROFILE_EXPONENT,
):
    """Return the power-law factor that maps anemometer-height speeds to the
    reference height.

    Returns ``1.0`` (identity) whenever either height is unset, so the
    correction is a no-op until the site geometry is configured.
    """
    if anemometer_height_m is None or reference_height_m is None:
        return 1.0
    return (reference_height_m / anemometer_height_m) ** exponent


def correct_to_reference_height(
    speed_m_s,
    anemometer_height_m=ANEMOMETER_HEIGHT_M,
    reference_height_m=REFERENCE_HEIGHT_M,
    exponent=WIND_PROFILE_EXPONENT,
):
    """Correct a wind speed measured at the anemometer height to the reference
    height using a power-law profile.

    With the default (unset) heights this returns ``speed_m_s`` unchanged.
    """
    return speed_m_s * height_correction_factor(
        anemometer_height_m, reference_height_m, exponent
    )
