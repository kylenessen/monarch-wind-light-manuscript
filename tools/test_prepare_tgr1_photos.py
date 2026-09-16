"""Check endpoint alignment without losing camera gaps or the calendar discontinuity."""

from datetime import datetime, timedelta
import unittest

from prepare_tgr1_photos import reconstruct_times


class Tgr1TimeTests(unittest.TestCase):
    def test_calendar_jump_preserves_elapsed_intervals_and_both_anchors(self):
        recorded = [datetime(2022, 10, 1, 19, 56, 4),
                    datetime(2022, 8, 31, 20, 6, 4),
                    datetime(2022, 8, 31, 20, 26, 4)]
        start = datetime(2024, 1, 2, 19, 30, 0, 663000)
        end = start + timedelta(minutes=33)
        result = reconstruct_times(recorded, start, end)
        self.assertEqual(result, [start, start + timedelta(minutes=11), end])

    def test_unexpected_clock_reversal_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unexpected camera clock jump"):
            reconstruct_times([datetime(2022, 9, 14), datetime(2022, 9, 13)],
                              datetime(2023, 12, 15), datetime(2024, 1, 5))


if __name__ == "__main__":
    unittest.main()
