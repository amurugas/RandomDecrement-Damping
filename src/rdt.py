import numpy as np


def random_decrement_signature(
    signal,
    fs,
    segment_seconds,
    threshold=None,
    threshold_factor=0.5,
    min_spacing_seconds=None,
    normalize=True,
):
    """
    Compute Random Decrement Signature using positive level upcrossings.

    Parameters
    ----------
    signal : array-like
        Bandpassed modal response signal.
    fs : float
        Sampling rate in Hz.
    segment_seconds : float
        Duration of each RDT segment.
    threshold : float | None
        Trigger threshold. If None, threshold_factor * std(signal) is used.
    threshold_factor : float
        Multiplier on signal standard deviation if threshold is None.
    min_spacing_seconds : float | None
        Minimum spacing between triggers. Helps avoid too many nearly repeated triggers.
    normalize : bool
        If True, normalize RDT signature by its initial value.

    Returns
    -------
    t : np.ndarray
        Time vector for RDT signature.
    rds : np.ndarray
        Random Decrement Signature.
    n_segments : int
        Number of averaged segments.
    threshold : float
        Trigger threshold used.
    """
    x = np.asarray(signal, dtype=float)
    x = x - np.nanmean(x)

    n_segment = int(round(segment_seconds * fs))

    if n_segment <= 0:
        raise ValueError("segment_seconds is too short.")

    if threshold is None:
        threshold = threshold_factor * np.nanstd(x)

    if min_spacing_seconds is None:
        min_spacing_samples = 1
    else:
        min_spacing_samples = int(round(min_spacing_seconds * fs))

    # Positive upcrossing of threshold
    candidate_triggers = np.where((x[:-1] < threshold) & (x[1:] >= threshold))[0] + 1

    # Keep only triggers where full segment is available
    candidate_triggers = candidate_triggers[candidate_triggers + n_segment <= len(x)]

    if len(candidate_triggers) == 0:
        raise ValueError("No RDT triggers found. Try lowering threshold_factor.")

    # Enforce minimum spacing between triggers
    triggers = []
    last_trigger = -10**18

    for idx in candidate_triggers:
        if idx - last_trigger >= min_spacing_samples:
            triggers.append(idx)
            last_trigger = idx

    if len(triggers) == 0:
        raise ValueError("No RDT triggers remain after spacing filter.")

    rds_sum = np.zeros(n_segment)

    for idx in triggers:
        rds_sum += x[idx:idx + n_segment]

    rds = rds_sum / len(triggers)

    if normalize:
        if abs(rds[0]) > 1e-20:
            rds = rds / abs(rds[0])

    t = np.arange(n_segment) / fs

    return t, rds, len(triggers), threshold