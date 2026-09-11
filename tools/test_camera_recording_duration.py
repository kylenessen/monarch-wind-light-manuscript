import unittest

from camera_recording_duration import summarize_camera


class DurationTests(unittest.TestCase):
    def test_old_clock_dates_duplicates_and_undated_media(self):
        rows = [{"capture_time": t, "status": "copied"} for t in [
            "2022-08-31T12:00:00", "2024-11-01T12:00:00",
            "2024-11-01T12:00:00", "2024-11-02T12:00:00", None,
        ]]
        result = summarize_camera("A", "D", rows, 24)
        self.assertEqual(result["main_run"]["span_days"], 1)
        self.assertEqual(result["main_run"]["photo_count"], 3)
        self.assertEqual(result["photos_outside_main_run"], 1)
        self.assertEqual(result["duplicate_timestamp_extra_photos"], 1)
        self.assertEqual(result["files_without_photo_timestamp"], 1)
        self.assertEqual(len(result["gaps_over_threshold"]), 1)

    def test_empty_and_single_photo_have_no_invented_runtime(self):
        self.assertIsNone(summarize_camera("A", "D", [], 24)["main_run"])
        result = summarize_camera("A", "D", [{"capture_time": "2025-01-01T00:00:00", "status": "copied"}], 24)
        self.assertEqual(result["main_run"]["span_days"], 0)
        self.assertIsNone(result["main_run"]["median_interval_seconds"])


if __name__ == "__main__":
    unittest.main()
