import unittest
from datetime import datetime, timedelta

import numpy as np

from src.alignment import SignalRecord, align_signal_records


class AlignSignalRecordsTests(unittest.TestCase):
    def test_same_start_trims_to_shortest_record(self):
        start = datetime(2026, 1, 1, 0, 0, 0)
        records = [
            SignalRecord("A", np.arange(5), 2.0, start),
            SignalRecord("B", np.arange(10, 16), 2.0, start),
        ]

        signals, fs, alignment = align_signal_records(records)

        self.assertEqual(fs, 2.0)
        np.testing.assert_array_equal(signals["A"], np.array([0, 1, 2, 3, 4]))
        np.testing.assert_array_equal(signals["B"], np.array([10, 11, 12, 13, 14]))
        self.assertEqual(alignment["A"]["source_start_index"], 0)
        self.assertEqual(alignment["B"]["source_end_index"], 5)

    def test_wall_clock_alignment_uses_common_overlap(self):
        start = datetime(2026, 1, 1, 0, 0, 0)
        records = [
            SignalRecord("early", np.arange(10), 2.0, start),
            SignalRecord("late", np.arange(100, 106), 2.0, start + timedelta(seconds=2)),
        ]

        signals, fs, alignment = align_signal_records(records, align_by_time=True)

        self.assertEqual(fs, 2.0)
        np.testing.assert_array_equal(signals["early"], np.array([4, 5, 6, 7, 8, 9]))
        np.testing.assert_array_equal(signals["late"], np.array([100, 101, 102, 103, 104, 105]))
        self.assertEqual(alignment["early"]["source_start_index"], 4)
        self.assertEqual(alignment["late"]["source_start_index"], 0)

    def test_wall_clock_alignment_rejects_no_overlap(self):
        start = datetime(2026, 1, 1, 0, 0, 0)
        records = [
            SignalRecord("A", np.arange(4), 2.0, start),
            SignalRecord("B", np.arange(4), 2.0, start + timedelta(seconds=3)),
        ]

        with self.assertRaisesRegex(ValueError, "No overlapping time range"):
            align_signal_records(records, align_by_time=True)


if __name__ == "__main__":
    unittest.main()
