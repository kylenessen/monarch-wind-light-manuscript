#!/usr/bin/env python3
"""Build normalized CSV tables for the USGS data release.

The source JSON, SQLite, and manuscript input files remain unchanged. Output is
written to ``data/release`` by default so the public tables can be reviewed
without disrupting the manuscript analyses.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

import pandas as pd


COUNT_VALUES = {
    "0": 0,
    "1-9": 1,
    "10-99": 10,
    "100-999": 100,
}

# SC1 and SC2 predate the explicit isNight field in the classification files.
# These intervals are the same intervals used by the manuscript preparation
# scripts to identify nighttime images.
LEGACY_NIGHT_PERIODS = {
    "SC1": (
        ("20231117174001", "20231118062001"),
        ("20231118172501", "20231119061501"),
        ("20231119171001", "20231120062001"),
        ("20231120172001", "20231121063001"),
    ),
    "SC2": (
        ("20231117172501", "20231118062001"),
        ("20231118171501", "20231119061501"),
    ),
}

TIMESTAMP_PATTERN = re.compile(r"_(\d{14})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create normalized CSV tables for the USGS data release."
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/release"))
    return parser.parse_args()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, na_rep="", lineterminator="\n")
    print(f"Wrote {len(frame):,} rows to {path}")


def format_timestamp_column(values: pd.Series, *, include_fraction: bool = False) -> pd.Series:
    timestamps = pd.to_datetime(values, format="mixed", errors="raise")
    if include_fraction:
        return timestamps.dt.strftime("%Y-%m-%d %H:%M:%S.%f").str.rstrip("0").str.rstrip(".")
    return timestamps.dt.strftime("%Y-%m-%d %H:%M:%S")


def prepare_deployments(source: Path) -> pd.DataFrame:
    deployments = pd.read_csv(source)
    deployments = deployments.rename(
        columns={
            "Deployed_time": "deployed_at_local",
            "Recovered_time": "recovered_at_local",
            "height_m": "camera_height_m",
            "horizontal_dist_to_cluster_m": "horizontal_distance_to_cluster_m",
            "view_direction": "view_direction_degrees",
            "Observer": "primary_observer",
            "youtube_url": "field_video_url",
            "wind_meter_name": "wind_sensor_name",
        }
    )
    deployments["deployed_at_local"] = format_timestamp_column(
        deployments["deployed_at_local"], include_fraction=True
    )
    deployments["recovered_at_local"] = format_timestamp_column(
        deployments["recovered_at_local"], include_fraction=True
    )
    columns = [
        "deployment_id",
        "grove",
        "camera_name",
        "wind_sensor_name",
        "deployed_at_local",
        "recovered_at_local",
        "camera_height_m",
        "horizontal_distance_to_cluster_m",
        "view_direction_degrees",
        "latitude",
        "longitude",
        "primary_observer",
        "view_id",
        "field_video_url",
        "notes",
    ]
    deployments = deployments[columns].sort_values("deployment_id").reset_index(drop=True)
    if deployments["deployment_id"].duplicated().any():
        raise ValueError("Deployment IDs must be unique")
    return deployments


def timestamp_from_filename(filename: str) -> tuple[str, str]:
    match = TIMESTAMP_PATTERN.search(filename)
    if match is None:
        raise ValueError(f"Image filename lacks a 14-digit timestamp: {filename}")
    compact = match.group(1)
    timestamp = pd.to_datetime(compact, format="%Y%m%d%H%M%S", errors="raise")
    return compact, timestamp.strftime("%Y-%m-%d %H:%M:%S")


def is_legacy_night(deployment_id: str, compact_timestamp: str) -> bool:
    return any(
        start <= compact_timestamp <= end
        for start, end in LEGACY_NIGHT_PERIODS.get(deployment_id, ())
    )


def prepare_classifications(json_dir: Path, deployments: pd.DataFrame) -> pd.DataFrame:
    observer_by_deployment = deployments.set_index("deployment_id")["primary_observer"].to_dict()
    records: list[dict[str, object]] = []

    for json_path in sorted(json_dir.glob("*.json")):
        deployment_id = json_path.stem
        if deployment_id not in observer_by_deployment:
            raise ValueError(f"Missing deployment metadata for {deployment_id}")
        data = json.loads(json_path.read_text())
        classifications = data.get("classifications", data)

        for image_filename, record in classifications.items():
            compact_timestamp, timestamp_local = timestamp_from_filename(image_filename)
            category_counts = {category: 0 for category in COUNT_VALUES}
            sun_category_counts = {category: 0 for category in COUNT_VALUES if category != "0"}

            for cell in record.get("cells", {}).values():
                category = str(cell.get("count", "0")).strip()
                if category not in COUNT_VALUES:
                    raise ValueError(
                        f"Unexpected classification category {category!r} in {image_filename}"
                    )
                category_counts[category] += 1
                direct_sun = bool(cell.get("directSun", cell.get("sunlight", False)))
                if direct_sun and category != "0":
                    sun_category_counts[category] += 1

            butterfly_index = sum(
                category_counts[category] * value
                for category, value in COUNT_VALUES.items()
            )
            sun_exposed_butterfly_index = sum(
                sun_category_counts.get(category, 0) * value
                for category, value in COUNT_VALUES.items()
            )
            record_night = record.get("isNight")
            if record_night is None:
                is_night = is_legacy_night(deployment_id, compact_timestamp)
                night_flag_source = "legacy_time_interval"
            else:
                is_night = bool(record_night)
                night_flag_source = "classification_record"

            records.append(
                {
                    "image_filename": image_filename,
                    "deployment_id": deployment_id,
                    "timestamp_local": timestamp_local,
                    "primary_observer": observer_by_deployment[deployment_id],
                    "record_user_id": record.get("user"),
                    "classification_confirmed": bool(record.get("confirmed", False)),
                    "is_night": is_night,
                    "night_flag_source": night_flag_source,
                    "cells_0": category_counts["0"],
                    "cells_1_9": category_counts["1-9"],
                    "cells_10_99": category_counts["10-99"],
                    "cells_100_999": category_counts["100-999"],
                    "sun_exposed_cells_1_9": sun_category_counts["1-9"],
                    "sun_exposed_cells_10_99": sun_category_counts["10-99"],
                    "sun_exposed_cells_100_999": sun_category_counts["100-999"],
                    "butterfly_index": butterfly_index,
                    "sun_exposed_butterfly_index": sun_exposed_butterfly_index,
                }
            )

    classifications = pd.DataFrame(records).sort_values(
        ["deployment_id", "timestamp_local", "image_filename"]
    ).reset_index(drop=True)
    if classifications.duplicated(["deployment_id", "image_filename"]).any():
        raise ValueError("Classification records must be unique by deployment and filename")
    if (classifications["sun_exposed_butterfly_index"] > classifications["butterfly_index"]).any():
        raise ValueError("Sun-exposed Butterfly Index cannot exceed total Butterfly Index")
    return classifications


def prepare_temperature(source: Path) -> pd.DataFrame:
    temperature = pd.read_csv(source)
    parsed_timestamp = pd.to_datetime(
        temperature["timestamp"].astype(str), format="%Y%m%d%H%M%S", errors="raise"
    )
    temperature = temperature.rename(
        columns={
            "filename": "image_filename",
            "temperature": "temperature_c",
            "confidence": "ocr_confidence",
        }
    )
    temperature["timestamp_local"] = parsed_timestamp.dt.strftime("%Y-%m-%d %H:%M:%S")
    temperature = temperature[
        [
            "image_filename",
            "deployment_id",
            "timestamp_local",
            "temperature_c",
            "ocr_confidence",
            "extraction_status",
        ]
    ].sort_values(["deployment_id", "timestamp_local", "image_filename"]).reset_index(drop=True)
    if temperature["image_filename"].duplicated().any():
        raise ValueError("Temperature image filenames must be unique")
    return temperature


def prepare_wind(
    wind_dir: Path, deployments: pd.DataFrame
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for deployment in deployments.itertuples(index=False):
        database_path = wind_dir / f"{deployment.wind_sensor_name}.s3db"
        if not database_path.exists():
            raise FileNotFoundError(
                f"Missing wind database for {deployment.deployment_id}: {database_path}"
            )
        start = pd.Timestamp(deployment.deployed_at_local).strftime("%Y-%m-%d %H:%M:%S")
        end = pd.Timestamp(deployment.recovered_at_local).strftime("%Y-%m-%d %H:%M:%S")
        query = """
            SELECT time AS timestamp_local,
                   speed AS wind_speed_m_s,
                   gust AS wind_gust_m_s,
                   direction AS wind_direction_degrees
            FROM Wind
            WHERE time BETWEEN ? AND ?
            ORDER BY time
        """
        with sqlite3.connect(database_path) as connection:
            frame = pd.read_sql_query(query, connection, params=[start, end])
        frame.insert(0, "wind_sensor_name", deployment.wind_sensor_name)
        frame.insert(0, "deployment_id", deployment.deployment_id)
        for column in ("wind_speed_m_s", "wind_gust_m_s", "wind_direction_degrees"):
            frame[column] = pd.to_numeric(frame[column].astype(str).str.strip(), errors="raise")
        frame["timestamp_local"] = format_timestamp_column(frame["timestamp_local"])
        frames.append(frame)

    wind = pd.concat(frames, ignore_index=True).sort_values(
        ["deployment_id", "timestamp_local"]
    ).reset_index(drop=True)
    if wind.duplicated(["deployment_id", "timestamp_local"]).any():
        raise ValueError("Wind measurements must be unique by deployment and timestamp")
    return wind


def main() -> int:
    args = parse_args()
    deployments = prepare_deployments(args.data_dir / "deployments.csv")
    classifications = prepare_classifications(args.data_dir / "deployments", deployments)
    temperature = prepare_temperature(args.data_dir / "temperature_data_2023.csv")
    wind = prepare_wind(args.data_dir / "wind", deployments)

    write_csv(deployments, args.output_dir / "deployments.csv")
    write_csv(classifications, args.output_dir / "classifications.csv")
    write_csv(temperature, args.output_dir / "temperature_measurements.csv")
    write_csv(wind, args.output_dir / "wind_measurements.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
