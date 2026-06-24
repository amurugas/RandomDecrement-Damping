import numpy as np
from scipy.signal import hilbert


def fit_exponential_decay(t, response, natural_frequency_hz, fit_start, fit_end):
    """
    Estimate damping from exponential decay envelope.

    For a lightly damped SDOF modal response:

        envelope(t) = A * exp(-alpha * t)

    and:

        zeta = alpha / omega_n

    Parameters
    ----------
    t : np.ndarray
        Time vector.
    response : np.ndarray
        Free-decay-like response.
    natural_frequency_hz : float
        Modal frequency in Hz.
    fit_start : float
        Fit start time in seconds.
    fit_end : float
        Fit end time in seconds.

    Returns
    -------
    result : dict
        Contains damping ratio, damping percent, alpha, envelope, fit curve, and R².
    """
    y = np.asarray(response, dtype=float)

    envelope = np.abs(hilbert(y))

    mask = (
        (t >= fit_start)
        & (t <= fit_end)
        & np.isfinite(envelope)
        & (envelope > 1e-12)
    )

    if np.sum(mask) < 10:
        raise ValueError("Not enough envelope points for exponential fit.")

    t_fit = t[mask]
    env_fit = envelope[mask]

    # log(envelope) = log(A) - alpha*t
    coeffs = np.polyfit(t_fit, np.log(env_fit), deg=1)

    slope = coeffs[0]
    intercept = coeffs[1]

    alpha = -slope
    A = np.exp(intercept)

    omega_n = 2 * np.pi * natural_frequency_hz
    zeta = alpha / omega_n

    envelope_fit = A * np.exp(-alpha * t)

    log_pred = intercept + slope * t_fit
    log_actual = np.log(env_fit)

    ss_res = np.sum((log_actual - log_pred) ** 2)
    ss_tot = np.sum((log_actual - np.mean(log_actual)) ** 2)

    if ss_tot > 0:
        r_squared = 1 - ss_res / ss_tot
    else:
        r_squared = np.nan

    return {
        "alpha": alpha,
        "zeta": zeta,
        "damping_percent": zeta * 100,
        "A": A,
        "envelope": envelope,
        "envelope_fit": envelope_fit,
        "fit_start": fit_start,
        "fit_end": fit_end,
        "r_squared": r_squared,
    }