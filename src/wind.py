"""Wind-speed unit conversion and height correction.

All wind-speed handling lives in this single module so that the
measured anemometer speed is converted (m/s -> mph) and corrected to a
common reference height exactly once, at the point the raw wind record
is consumed (``src.io.read_wind_file``). Downstream scripts consume the
already-corrected, already-converted columns and must not re-derive the
conversion factor or the height-correction profile themselves.

Reference-height correction uses the power-law wind profile:

    U(z_target) = U(z_meas) * (z_target / z_meas) ** exponent

where ``exponent`` is the terrain/atmospheric boundary-layer exponent
(commonly ~0.14 for open terrain, higher for urban/suburban terrain).

The site-specific heights are unknown until configured, so the defaults
below are an identity correction (``REFERENCE_HEIGHT_M`` ==
``ANEMOMETER_HEIGHT_M`` => factor 1.0). Set the two heights to the real
anemometer and reference (e.g. roof) elevations to enable the
correction; no other file needs to change.
"""

# --- Unit conversion -------------------------------------------------------

#: Miles per hour per meter per second (exact).
MPH_PER_MPS = 2.2369362920544


# --- Height-correction (power-law wind profile) parameters -----------------

#: Height above ground of the anemometer that recorded the raw wind data [m].
ANEMOMETER_HEIGHT_M = 1.0

#: Reference height the wind speed is corrected to (e.g. roof level) [m].
#: Defaults to the anemometer height so the correction is an identity until
#: real site heights are supplied.
REFERENCE_HEIGHT_M = 1.0

#: Power-law exponent of the wind profile (terrain dependent).
WIND_PROFILE_EXPONENT = 0.14


def mps_to_mph(wind_mps):
    """Convert a wind speed (scalar or array) from m/s to mph."""
    return wind_mps * MPH_PER_MPS


def height_correction_factor(
    sensor_height_m=ANEMOMETER_HEIGHT_M,
    reference_height_m=REFERENCE_HEIGHT_M,
    exponent=WIND_PROFILE_EXPONENT,
):
    """Return the multiplicative power-law factor from sensor to reference height.

    Returns 1.0 when ``reference_height_m == sensor_height_m``.
    """
    if sensor_height_m <= 0:
        raise ValueError("sensor_height_m must be positive.")
    if reference_height_m <= 0:
        raise ValueError("reference_height_m must be positive.")

    return (reference_height_m / sensor_height_m) ** exponent


def correct_to_reference_height(
    wind_mps,
    sensor_height_m=ANEMOMETER_HEIGHT_M,
    reference_height_m=REFERENCE_HEIGHT_M,
    exponent=WIND_PROFILE_EXPONENT,
):
    """Correct a measured wind speed (m/s) to the reference height (m/s)."""
    factor = height_correction_factor(
        sensor_height_m=sensor_height_m,
        reference_height_m=reference_height_m,
        exponent=exponent,
    )
    return wind_mps * factor
