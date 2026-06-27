from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np


@dataclass(frozen=True)
class SignalRecord:
    channel: str
    values: np.ndarray
    fs: float
    start_time: datetime

    @property
    def end_time(self):
        return self.start_time + timedelta(seconds=len(self.values) / self.fs)


def align_signal_records(records, align_by_time=False):
    """
    Return equal-length signal arrays, either by simple truncation or by
    wall-clock overlap.
    """
    if not records:
        raise ValueError("No signal records provided")

    fs_values = np.array([record.fs for record in records], dtype=float)

    if not np.allclose(fs_values, fs_values[0]):
        raise ValueError(f"Sampling rates do not match: {fs_values}")

    fs = float(fs_values[0])

    if not align_by_time:
        n_samples = min(len(record.values) for record in records)
        signals = {
            record.channel: np.asarray(record.values[:n_samples], dtype=float)
            for record in records
        }
        alignment = {
            record.channel: {
                "start_time": record.start_time,
                "source_start_index": 0,
                "source_end_index": n_samples,
                "offset_sec": 0.0,
            }
            for record in records
        }
        return signals, fs, alignment

    overlap_start = max(record.start_time for record in records)
    overlap_end = min(record.end_time for record in records)
    overlap_duration_sec = (overlap_end - overlap_start).total_seconds()
    n_samples = int(np.floor(overlap_duration_sec * fs + 1e-9))

    if n_samples <= 0:
        raise ValueError(
            "No overlapping time range across channels: "
            f"{overlap_start} to {overlap_end}"
        )

    signals = {}
    alignment = {}

    for record in records:
        offset_sec = (overlap_start - record.start_time).total_seconds()
        start_idx_float = offset_sec * fs
        start_idx = int(round(start_idx_float))

        if not np.isclose(start_idx_float, start_idx, atol=1e-6):
            raise ValueError(
                f"Non-integer sample offset for {record.channel}: "
                f"{start_idx_float:.6f} samples"
            )

        end_idx = start_idx + n_samples

        if start_idx < 0 or end_idx > len(record.values):
            raise ValueError(
                f"Aligned sample range is outside {record.channel}: "
                f"{start_idx}:{end_idx} for {len(record.values)} samples"
            )

        signals[record.channel] = np.asarray(record.values[start_idx:end_idx], dtype=float)
        alignment[record.channel] = {
            "start_time": record.start_time,
            "source_start_index": start_idx,
            "source_end_index": end_idx,
            "offset_sec": offset_sec,
        }

    return signals, fs, alignment
