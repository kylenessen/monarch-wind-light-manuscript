#!/usr/bin/env python3
"""Regenerate retained analysis datasets under alternative BI category values."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ANALYSIS_DIR = Path(__file__).resolve().parent
REPO_DIR = ANALYSIS_DIR.parent
sys.path.insert(0, str(ANALYSIS_DIR))

from release_schema import analysis_30_minute, analysis_next_day

import prepare_dynamic_windows as dynamic  # noqa: E402
import prepare_lag_30min as lag30  # noqa: E402


CATEGORY_MAPPINGS = {
    "lower_bound": {
        "0": 0,
        "1-9": 1,
        "10-99": 10,
        "100-999": 100,
        "1000+": 1000,
    },
    "geometric_midpoint": {
        "0": 0,
        "1-9": 3,
        "10-99": 32,
        "100-999": 316,
        "1000+": 1000,
    },
    "arithmetic_midpoint": {
        "0": 0,
        "1-9": 5,
        "10-99": 55,
        "100-999": 550,
        "1000+": 1000,
    },
    "upper_bound": {
        "0": 0,
        "1-9": 9,
        "10-99": 99,
        "100-999": 999,
        "1000+": 1000,
    },
}


def prepare_30_minute(mapping: dict[str, int]) -> pd.DataFrame:
    deployments = lag30.load_deployments(REPO_DIR / "data/deployments.csv")
    processor = lag30.ButterflyCountProcessor()
    processor.COUNT_MAPPING = mapping
    observations = processor.process_deployments(REPO_DIR / "data/deployments")
    observations = lag30.add_temperature_data(
        observations,
        REPO_DIR / "data/temperature_data_2023.csv",
    )
    paired = lag30.create_lag_analysis(
        observations,
        lag_minutes=30,
        remove_zero_pairs=True,
        tolerance_minutes=5,
    )
    paired = lag30.add_wind_data(
        paired,
        deployments,
        wind_db_dir=REPO_DIR / "data/wind",
        lag_minutes=30,
    )
    return lag30.add_deployment_metadata(paired, deployments)


def prepare_next_day(mapping: dict[str, int]) -> pd.DataFrame:
    deployments = pd.read_csv(REPO_DIR / "data/deployments.csv")
    processor = dynamic.DailyButterflyProcessor()
    processor.COUNT_MAPPING = mapping
    observations = processor.process_deployments(REPO_DIR / "data/deployments")
    observations, temperatures = dynamic.add_temperature_data(
        observations,
        REPO_DIR / "data/temperature_data_2023.csv",
    )
    daily = dynamic.create_daily_aggregates_with_final_observation(observations)
    valid_days = dynamic.filter_valid_days(daily, min_photos=15, max_photos=25)
    return dynamic.create_dynamic_lag_pairs(
        valid_days,
        observations,
        temperatures,
        deployments,
        REPO_DIR / "data/wind",
        window_type="nextday",
    )


def validate_lower_bound(
    generated_30: pd.DataFrame,
    generated_next: pd.DataFrame,
) -> None:
    existing_30 = pd.read_csv(REPO_DIR / "data/monarch_analysis_lag30min.csv")
    keys_30 = ["deployment_id", "image_filename_t", "image_filename_t_lag"]
    columns_30 = [
        "total_butterflies_t",
        "total_butterflies_t_lag",
        "butterflies_direct_sun_t",
        "butterflies_direct_sun_t_lag",
        "butterfly_difference",
    ]
    left_30 = generated_30.sort_values(keys_30).reset_index(drop=True)
    right_30 = existing_30.sort_values(keys_30).reset_index(drop=True)
    if not left_30[keys_30].equals(right_30[keys_30]):
        raise RuntimeError("Regenerated 30-minute pair identities do not match source data")
    if not np.allclose(left_30[columns_30], right_30[columns_30], equal_nan=True):
        raise RuntimeError("Regenerated 30-minute BI values do not match source data")

    existing_next = pd.read_csv(
        REPO_DIR / "data/monarch_daily_lag_analysis_nextday_window.csv"
    )
    keys_next = ["deployment_id", "deployment_day_id_t", "deployment_day_id_t_1"]
    columns_next = [
        "max_butterflies_t",
        "max_butterflies_t_1",
        "sum_butterflies_direct_sun",
        "butterfly_diff",
    ]
    left_next = generated_next.sort_values(keys_next).reset_index(drop=True)
    right_next = existing_next.sort_values(keys_next).reset_index(drop=True)
    if not left_next[keys_next].equals(right_next[keys_next]):
        raise RuntimeError("Regenerated Next Day pair identities do not match source data")
    if not np.allclose(
        left_next[columns_next],
        right_next[columns_next],
        equal_nan=True,
    ):
        raise RuntimeError("Regenerated Next Day BI values do not match source data")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_DIR / "analysis/outputs/bi_category_sensitivity/data",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for name, mapping in CATEGORY_MAPPINGS.items():
        print(f"Preparing BI sensitivity mapping {name}: {mapping}")
        data_30 = prepare_30_minute(mapping)
        data_next = prepare_next_day(mapping)
        if name == "lower_bound":
            validate_lower_bound(data_30, data_next)
        analysis_30_minute(data_30).to_csv(args.output_dir / f"30_minute_{name}.csv", index=False)
        analysis_next_day(data_next).to_csv(args.output_dir / f"next_day_{name}.csv", index=False)


if __name__ == "__main__":
    main()
