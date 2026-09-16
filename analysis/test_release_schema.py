"""Regression checks for scientific selection and preservation of analysis inputs."""

import unittest
from pathlib import Path

import pandas as pd

from release_schema import (
    NEXT_COLUMNS, THIRTY_COLUMNS, analysis_30_minute, analysis_next_day,
    has_classification,
)

ROOT = Path(__file__).resolve().parents[1]


class ReleaseSchemaTests(unittest.TestCase):
    def test_zero_requires_evidence_but_saved_annotations_do_not_require_confirmation(self):
        untouched = {"confirmed": False, "cells": {"a": {"count": "0"}}}
        self.assertFalse(has_classification(untouched))
        self.assertTrue(has_classification({**untouched, "confirmed": True}))
        self.assertTrue(has_classification({**untouched, "user": "observer"}))
        self.assertTrue(has_classification({"cells": {"a": {"count": "1-9"}}}))

    def test_thirty_minute_preserves_every_selected_value_and_order(self):
        source = pd.read_csv(ROOT / "data/monarch_analysis_lag30min.csv")
        released = analysis_30_minute(source)
        self.assertEqual(len(released), 1894)
        pd.testing.assert_frame_equal(released.rename(columns={v: k for k, v in THIRTY_COLUMNS.items()}), source[list(THIRTY_COLUMNS)])
        self.assertNotIn("minutes_since_sunrise", released)

    def test_next_day_preserves_historical_complete_case_selection(self):
        source = pd.read_csv(ROOT / "data/monarch_daily_lag_analysis_nextday_window.csv")
        selected = source.loc[source.metrics_complete.ge(.95) & source[list(NEXT_COLUMNS)].notna().all(axis=1)]
        selected = selected.sort_values(["deployment_id", "observation_order_t"]).reset_index(drop=True)
        released = analysis_next_day(source)
        self.assertEqual(len(released), 96)
        pd.testing.assert_frame_equal(released.rename(columns={v: k for k, v in NEXT_COLUMNS.items()}), selected[list(NEXT_COLUMNS)])

    def test_inconsistent_response_fails_instead_of_exporting_silent_error(self):
        source = pd.read_csv(ROOT / "data/monarch_analysis_lag30min.csv").head(2).copy()
        source.loc[0, "butterfly_difference"] += 1
        with self.assertRaises(AssertionError):
            analysis_30_minute(source)


if __name__ == "__main__":
    unittest.main()
