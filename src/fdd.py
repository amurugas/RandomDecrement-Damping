from pathlib import Path

import numpy as np
from scipy.signal import csd


def build_csd_matrix(signals, fs, nperseg=131072, noverlap=None):
    """
    Build cross-spectral density matrix G(f) for multi-channel data.

    Parameters
    ----------
    signals : dict[str, np.ndarray]
        Dictionary of channel name -> acceleration time history.
    fs : float
        Sampling rate in Hz.
    nperseg : int
        Welch segment length.
    noverlap : int | None
        Overlap for Welch/CSD.

    Returns
    -------
    f : np.ndarray
        Frequency vector.
    G : np.ndarray
        Cross-spectral density matrix with shape:
        [n_freq, n_channels, n_channels]
    channels : list[str]
        Channel order used in G.
    """
    channels = list(signals.keys())
    n_channels = len(channels)

    f_ref = None
    csd_pairs = {}

    for i, ch_i in enumerate(channels):
        for j, ch_j in enumerate(channels):
            f, Pij = csd(
                signals[ch_i],
                signals[ch_j],
                fs=fs,
                nperseg=nperseg,
                noverlap=noverlap,
                detrend="constant",
                scaling="density",
            )

            if f_ref is None:
                f_ref = f

            csd_pairs[(i, j)] = Pij

    n_freq = len(f_ref)
    G = np.zeros((n_freq, n_channels, n_channels), dtype=complex)

    for (i, j), Pij in csd_pairs.items():
        G[:, i, j] = Pij

    return f_ref, G, channels


def compute_fdd(G):
    """
    Run SVD at every frequency line.

    Parameters
    ----------
    G : np.ndarray
        CSD matrix with shape [n_freq, n_channels, n_channels].

    Returns
    -------
    singular_values : np.ndarray
        Shape [n_freq, n_channels].
    mode_shapes : np.ndarray
        Shape [n_freq, n_channels, n_channels].
        First mode shape at frequency k is mode_shapes[k, :, 0].
    """
    n_freq = G.shape[0]
    n_channels = G.shape[1]

    singular_values = np.zeros((n_freq, n_channels))
    mode_shapes = np.zeros((n_freq, n_channels, n_channels), dtype=complex)

    for k in range(n_freq):
        U, S, _ = np.linalg.svd(G[k])
        singular_values[k, :] = S
        mode_shapes[k, :, :] = U

    return singular_values, mode_shapes