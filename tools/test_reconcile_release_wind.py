import unittest
import pandas as pd
from reconcile_release_wind import deduplicate, interval_matches, normalize


def frame(rows):
    result = pd.DataFrame(rows, columns=["wind_sensor_name", "timestamp_recorded", "wind_speed_m_s", "wind_gust_m_s", "wind_direction_degrees", "source_database"])
    return normalize(result)


class WindTests(unittest.TestCase):
    def test_duplicates_ignore_database_but_preserve_sensor_and_conflicts(self):
        source = frame([
            ["A", "2025-01-01 12:00:00", " 0.1", "2.0", "90", "one"],
            ["A", "2025-01-01T12:00:00", 0.1, 2, 90, "two"],
            ["A", "2025-01-01 12:00:00", 0.1, 3, 90, "three"],
            ["B", "2025-01-01 12:00:00", 0.1, 2, 90, "four"],
        ])
        unique, links = deduplicate(source)
        self.assertEqual(len(unique), 3)
        self.assertEqual(len(links), 4)
        self.assertEqual(sorted(unique.source_record_count), [1, 1, 2])
        self.assertEqual(int(unique.timestamp_conflict.sum()), 2)

    def test_boundaries_are_inclusive_and_fractional(self):
        source = frame([["A", f"2025-01-01 12:00:0{i}", 0, 0, 0, "one"] for i in range(4)])
        self.assertEqual(list(interval_matches(source, pd.Timestamp("2025-01-01 12:00:00.5"), pd.Timestamp("2025-01-01 12:00:02"))), [False, True, True, False])

    def test_missing_measurements_deduplicate_without_becoming_zero(self):
        source = frame([["A", "2025-01-01", None, 0, 0, "one"], ["A", "2025-01-01", None, 0, 0, "two"]])
        unique, links = deduplicate(source)
        self.assertEqual(len(unique), 1)
        self.assertTrue(pd.isna(unique.iloc[0].wind_speed_m_s))
        self.assertEqual(len(links), 2)


if __name__ == "__main__":
    unittest.main()
