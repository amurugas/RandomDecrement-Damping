import numpy as np
from scipy.signal import butter, sosfiltfilt


def bandpass_filter(signal, fs, f_low, f_high, order=4):
    """
    Zero-phase Butterworth bandpass filter.

    Parameters
    ----------
    signal : array-like
        Input acceleration signal.
    fs : float
        Sampling rate in Hz.
    f_low : float
        Lower cutoff frequency in Hz.
    f_high : float
        Upper cutoff frequency in Hz.
    order : int
        Butterworth filter order.

    Returns
    -------
    filtered : np.ndarray
        Bandpass-filtered signal.
    """
    x = np.asarray(signal, dtype=float)

    sos = butter(
        N=order,
        Wn=[f_low, f_high],
        btype="bandpass",
        fs=fs,
        output="sos",
    )

    filtered = sosfiltfilt(sos, x)

    return filtered