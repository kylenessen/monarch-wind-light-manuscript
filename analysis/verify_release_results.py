#!/usr/bin/env python3
"""Compare result tables from runs before and after the public schema migration.

Run with uv run analysis/verify_release_results.py BASELINE_OUTPUT_DIRECTORY.
Only known variable renames and the coverage-note wording are normalized.
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from release_schema import THIRTY_COLUMNS, NEXT_COLUMNS


RENAMES = {**THIRTY_COLUMNS, **NEXT_COLUMNS,
           "butterfly_diff_sqrt": "delta_bi_signed_square_root"}


def normalize(text):
    result = str(text)
    for old, new in sorted(RENAMES.items(), key=lambda pair: -len(pair[0])):
        if old != new:
            result = result.replace("X" + old, "X" + new)
            result = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(old) + r"(?![A-Za-z0-9_])", new, result)
    return result.replace("metrics_complete >= 0.95", "release table selected at overall coverage >= 0.95")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("--current", type=Path, default=Path("analysis/outputs"))
    parser.add_argument("--report", type=Path, default=Path("data/release_working/analysis_verification.json"))
    args = parser.parse_args()
    results, failures = [], []
    folders = ["descriptive_statistics", "descriptive_figures", "wind_at_clusters",
               "harmonized_model_comparison", "next_day_window", "bi_category_sensitivity"]
    for folder in folders:
        for path in sorted((args.baseline / folder).glob("*.csv")):
            relative = path.relative_to(args.baseline)
            left, right = pd.read_csv(path), pd.read_csv(args.current / relative)
            left = left.rename(columns=RENAMES)
            if list(left.columns) != list(right.columns) or left.shape != right.shape:
                failures.append(f"{relative} schema or row count")
                continue
            maximum_difference = 0.0
            for column in left:
                x, y = left[column], right[column]
                if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
                    if not np.allclose(x, y, equal_nan=True, rtol=1e-10, atol=1e-10):
                        failures.append(f"{relative} numeric column {column}")
                    difference = (x - y).abs().max()
                    if pd.notna(difference):
                        maximum_difference = max(maximum_difference, float(difference))
                elif not x.map(normalize).equals(y.map(str)):
                    failures.append(f"{relative} text column {column}")
            results.append(dict(file=str(relative), rows=len(right),
                                maximum_absolute_numeric_difference=maximum_difference))
    if not results:
        raise ValueError("No baseline result tables found")
    report = dict(comparison="Historical results versus release-schema results. Only documented variable renames are normalized.",
                  numeric_tolerance=dict(relative=1e-10, absolute=1e-10), files=results, failures=failures)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(compared_tables=len(results), failures=failures,
                         maximum_absolute_difference=max(r["maximum_absolute_numeric_difference"] for r in results)), indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
