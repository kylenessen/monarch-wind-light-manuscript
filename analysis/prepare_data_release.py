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

import numpy as np
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

FIELD_METADATA = {
    "deployments": {
        "deployment_id": ("Unique identifier for a camera and wind-sensor deployment.", "N/A"),
        "grove": ("Monarch overwintering grove where the equipment was deployed.", "N/A"),
        "camera_name": ("Field name assigned to the trail camera.", "N/A"),
        "wind_sensor_name": (
            "Field name assigned to the wind sensor and used in the source database filename.",
            "N/A",
        ),
        "deployed_at_local": ("Local date and time when the deployment began.", "PST"),
        "recovered_at_local": ("Local date and time when the deployment ended.", "PST"),
        "camera_height_m": ("Height of the camera above the ground.", "meters"),
        "horizontal_distance_to_cluster_m": (
            "Estimated horizontal distance from the camera to the monitored monarch cluster.",
            "meters",
        ),
        "view_direction_degrees": (
            "Compass direction in which the camera faced, measured clockwise from north.",
            "degrees",
        ),
        "latitude": ("Latitude of the deployment location.", "decimal degrees"),
        "longitude": ("Longitude of the deployment location.", "decimal degrees"),
        "primary_observer": (
            "Name of the primary person responsible for classifying images from the deployment.",
            "N/A",
        ),
        "view_id": ("Identifier for the monitored camera view.", "N/A"),
        "field_video_url": ("URL for the deployment field video, when available.", "N/A"),
        "notes": ("Field notes associated with the deployment.", "N/A"),
    },
    "classifications": {
        "image_filename": ("Canonical filename of the classified image.", "N/A"),
        "deployment_id": ("Deployment identifier encoded in the image filename.", "N/A"),
        "timestamp_local": ("Image acquisition date and time parsed from the filename.", "PST"),
        "primary_observer": (
            "Primary image classifier assigned to the deployment.", "N/A"
        ),
        "record_user_id": (
            "User identifier stored with the final classification record. This can identify a later reviewer or editor.",
            "N/A",
        ),
        "classification_confirmed": (
            "Whether the classification software marked the image record as confirmed.",
            "boolean",
        ),
        "is_night": ("Whether the image was identified as a nighttime image.", "boolean"),
        "night_flag_source": (
            "Source used for the nighttime indicator, either the classification record or a legacy time interval.",
            "N/A",
        ),
        "cells_0": ("Number of image grid cells classified as containing zero butterflies.", "integer"),
        "cells_1_9": ("Number of image grid cells classified in the 1 to 9 category.", "integer"),
        "cells_10_99": ("Number of image grid cells classified in the 10 to 99 category.", "integer"),
        "cells_100_999": (
            "Number of image grid cells classified in the 100 to 999 category.", "integer"
        ),
        "sun_exposed_cells_1_9": (
            "Number of directly sun-exposed occupied cells in the 1 to 9 category.",
            "integer",
        ),
        "sun_exposed_cells_10_99": (
            "Number of directly sun-exposed occupied cells in the 10 to 99 category.",
            "integer",
        ),
        "sun_exposed_cells_100_999": (
            "Number of directly sun-exposed occupied cells in the 100 to 999 category.",
            "integer",
        ),
        "butterfly_index": (
            "Visible cluster-size index calculated with category lower bounds of 0, 1, 10, and 100.",
            "Butterfly Index units",
        ),
        "sun_exposed_butterfly_index": (
            "Butterfly Index subtotal from occupied cells classified as receiving direct sunlight.",
            "Butterfly Index units",
        ),
    },
    "temperature_measurements": {
        "image_filename": ("Canonical filename of the source image.", "N/A"),
        "deployment_id": ("Deployment identifier encoded in the image filename.", "N/A"),
        "timestamp_local": ("Image acquisition date and time parsed from the filename.", "PST"),
        "temperature_c": (
            "Approximate local temperature extracted from the camera image overlay and reviewed manually.",
            "degrees Celsius",
        ),
        "ocr_confidence": ("Confidence score recorded by the OCR extraction workflow.", "proportion"),
        "extraction_status": (
            "Whether the temperature came from successful OCR or manual entry.", "N/A"
        ),
    },
    "wind_measurements": {
        "deployment_id": ("Deployment associated with the wind measurement.", "N/A"),
        "wind_sensor_name": ("Field name assigned to the wind sensor.", "N/A"),
        "timestamp_local": ("Local date and time of the wind measurement.", "PST"),
        "wind_speed_m_s": ("Sustained wind speed recorded by the sensor.", "meters per second"),
        "wind_gust_m_s": ("Wind gust speed recorded by the sensor.", "meters per second"),
        "wind_direction_degrees": (
            "Wind direction recorded by the sensor, measured clockwise from north.",
            "degrees",
        ),
    },
    "analysis_30_minute": {
        "deployment_id": ("Deployment associated with the paired observations.", "N/A"),
        "deployment_day_id": ("Unique identifier for a deployment and calendar day.", "N/A"),
        "observation_order": ("Sequential position of the current image within its deployment day.", "integer"),
        "previous_image_filename": ("Filename of the earlier image in the pair.", "N/A"),
        "previous_timestamp_local": ("Acquisition date and time of the earlier image.", "PST"),
        "current_image_filename": ("Filename of the later image in the pair.", "N/A"),
        "current_timestamp_local": ("Acquisition date and time of the later image.", "PST"),
        "lag_minutes": ("Elapsed time between the paired images.", "minutes"),
        "previous_butterfly_index": ("Butterfly Index in the earlier image.", "Butterfly Index units"),
        "current_butterfly_index": ("Butterfly Index in the later image.", "Butterfly Index units"),
        "butterfly_index_change": (
            "Current Butterfly Index minus previous Butterfly Index.", "Butterfly Index units"
        ),
        "butterfly_index_change_signed_cuberoot": (
            "Signed cube-root transformation of Butterfly Index change used as the model response.",
            "transformed Butterfly Index units",
        ),
        "previous_sun_exposed_butterfly_index": (
            "Sun-exposed Butterfly Index in the earlier image.", "Butterfly Index units"
        ),
        "previous_temperature_c": ("Approximate local temperature in the earlier image.", "degrees Celsius"),
        "current_temperature_c": ("Approximate local temperature in the later image.", "degrees Celsius"),
        "mean_temperature_c": ("Mean temperature of the paired images.", "degrees Celsius"),
        "maximum_wind_gust_m_s": (
            "Maximum recorded wind gust between the paired images.", "meters per second"
        ),
        "minutes_since_sunrise": ("Minutes elapsed since local sunrise for the current image.", "minutes"),
        "primary_observer": ("Primary image classifier assigned to the deployment.", "N/A"),
    },
    "analysis_next_day": {
        "deployment_id": ("Deployment associated with the paired monitoring days.", "N/A"),
        "observation_order": ("Sequential position of the current day within the deployment series.", "integer"),
        "previous_date": ("Calendar date of the previous monitoring day.", "PST date"),
        "current_date": ("Calendar date of the current monitoring day.", "PST date"),
        "previous_day_maximum_timestamp_local": (
            "Date and time of maximum Butterfly Index on the previous day.", "PST"
        ),
        "current_day_maximum_timestamp_local": (
            "Date and time of maximum Butterfly Index on the current day.", "PST"
        ),
        "window_start_local": (
            "Beginning of the analysis window at the previous day's maximum Butterfly Index.",
            "PST",
        ),
        "window_end_local": (
            "End of the analysis window at the current day's final daytime image.", "PST"
        ),
        "window_duration_hours": ("Duration of the analysis window.", "hours"),
        "overall_data_completeness": (
            "Geometric mean of temperature, wind, and image data coverage.", "proportion"
        ),
        "temperature_data_coverage": (
            "Proportion of expected temperature observations present in the window.", "proportion"
        ),
        "wind_data_coverage": (
            "Proportion of expected wind observations present in the window.", "proportion"
        ),
        "image_data_coverage": (
            "Proportion of expected daylight image observations present in the window.", "proportion"
        ),
        "previous_day_maximum_butterfly_index": (
            "Maximum Butterfly Index on the previous monitoring day.", "Butterfly Index units"
        ),
        "current_day_maximum_butterfly_index": (
            "Maximum Butterfly Index on the current monitoring day.", "Butterfly Index units"
        ),
        "butterfly_index_change": (
            "Current-day maximum Butterfly Index minus previous-day maximum Butterfly Index.",
            "Butterfly Index units",
        ),
        "butterfly_index_change_signed_square_root": (
            "Signed square-root transformation of maximum Butterfly Index change used as the model response.",
            "transformed Butterfly Index units",
        ),
        "minimum_temperature_c": ("Minimum temperature in the analysis window.", "degrees Celsius"),
        "maximum_temperature_c": ("Maximum temperature in the analysis window.", "degrees Celsius"),
        "temperature_at_previous_day_maximum_c": (
            "Temperature at the previous day's maximum Butterfly Index.", "degrees Celsius"
        ),
        "maximum_wind_gust_m_s": (
            "Maximum recorded wind gust in the analysis window.", "meters per second"
        ),
        "cumulative_sun_exposed_butterfly_index": (
            "Sum of sun-exposed Butterfly Index across daylight images in the analysis window.",
            "Butterfly Index units",
        ),
        "primary_observer": ("Primary image classifier assigned to the deployment.", "N/A"),
    },
}


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


def prepare_analysis_30_minute(source: Path) -> pd.DataFrame:
    analysis = pd.read_csv(source)
    expected_change = analysis["total_butterflies_t"] - analysis["total_butterflies_t_lag"]
    expected_cuberoot = np.cbrt(expected_change)
    if not np.allclose(analysis["butterfly_difference"], expected_change):
        raise ValueError("The 30-minute Butterfly Index changes do not match their source values")
    if not np.allclose(analysis["butterfly_difference_cbrt"], expected_cuberoot):
        raise ValueError("The 30-minute signed cube-root responses are inconsistent")

    columns = {
        "deployment_id": "deployment_id",
        "deployment_day": "deployment_day_id",
        "observation_order_within_day_t": "observation_order",
        "image_filename_t_lag": "previous_image_filename",
        "timestamp_t_lag": "previous_timestamp_local",
        "image_filename_t": "current_image_filename",
        "timestamp_t": "current_timestamp_local",
        "actual_lag_minutes": "lag_minutes",
        "total_butterflies_t_lag": "previous_butterfly_index",
        "total_butterflies_t": "current_butterfly_index",
        "butterfly_difference": "butterfly_index_change",
        "butterfly_difference_cbrt": "butterfly_index_change_signed_cuberoot",
        "butterflies_direct_sun_t_lag": "previous_sun_exposed_butterfly_index",
        "temperature_t_lag": "previous_temperature_c",
        "temperature_t": "current_temperature_c",
        "temperature_avg": "mean_temperature_c",
        "max_gust": "maximum_wind_gust_m_s",
        "time_within_day_t": "minutes_since_sunrise",
        "Observer": "primary_observer",
    }
    output = analysis[list(columns)].rename(columns=columns)
    output = output.sort_values(
        ["deployment_id", "deployment_day_id", "observation_order"]
    ).reset_index(drop=True)
    if output[
        [
            "butterfly_index_change_signed_cuberoot",
            "previous_butterfly_index",
            "maximum_wind_gust_m_s",
            "mean_temperature_c",
            "previous_sun_exposed_butterfly_index",
            "minutes_since_sunrise",
            "observation_order",
            "deployment_day_id",
            "deployment_id",
        ]
    ].isna().any().any():
        raise ValueError("The 30-minute release table contains missing model inputs")
    return output


def prepare_analysis_next_day(source: Path) -> pd.DataFrame:
    analysis = pd.read_csv(source)
    required = [
        "butterfly_diff",
        "max_butterflies_t_1",
        "lag_duration_hours",
        "temp_min",
        "temp_max",
        "temp_at_max_count_t_1",
        "wind_max_gust",
        "sum_butterflies_direct_sun",
        "observation_order_t",
        "deployment_id",
    ]
    analysis = analysis.loc[
        analysis["metrics_complete"].ge(0.95) & analysis[required].notna().all(axis=1)
    ].copy()
    expected_change = analysis["max_butterflies_t"] - analysis["max_butterflies_t_1"]
    expected_sqrt = np.sign(expected_change) * np.sqrt(np.abs(expected_change))
    if not np.allclose(analysis["butterfly_diff"], expected_change):
        raise ValueError("The next-day Butterfly Index changes do not match their source values")

    analysis["butterfly_index_change_signed_square_root"] = expected_sqrt
    columns = {
        "deployment_id": "deployment_id",
        "observation_order_t": "observation_order",
        "date_t_1": "previous_date",
        "date_t": "current_date",
        "time_of_max_t_1": "previous_day_maximum_timestamp_local",
        "time_of_max_t": "current_day_maximum_timestamp_local",
        "window_start": "window_start_local",
        "window_end": "window_end_local",
        "lag_duration_hours": "window_duration_hours",
        "metrics_complete": "overall_data_completeness",
        "temp_data_coverage": "temperature_data_coverage",
        "wind_data_coverage": "wind_data_coverage",
        "butterfly_data_coverage": "image_data_coverage",
        "max_butterflies_t_1": "previous_day_maximum_butterfly_index",
        "max_butterflies_t": "current_day_maximum_butterfly_index",
        "butterfly_diff": "butterfly_index_change",
        "butterfly_index_change_signed_square_root": "butterfly_index_change_signed_square_root",
        "temp_min": "minimum_temperature_c",
        "temp_max": "maximum_temperature_c",
        "temp_at_max_count_t_1": "temperature_at_previous_day_maximum_c",
        "wind_max_gust": "maximum_wind_gust_m_s",
        "sum_butterflies_direct_sun": "cumulative_sun_exposed_butterfly_index",
        "Observer": "primary_observer",
    }
    output = analysis[list(columns)].rename(columns=columns)
    return output.sort_values(["deployment_id", "observation_order"]).reset_index(drop=True)


def format_range_value(value: object) -> str:
    if isinstance(value, (bool, np.bool_)):
        return str(bool(value))
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.15g}"
    return str(value)


def field_range(series: pd.Series, units: str) -> tuple[str, str]:
    values = series.dropna()
    if values.empty:
        return "N/A", "N/A"
    if pd.api.types.is_bool_dtype(values):
        return format_range_value(values.min()), format_range_value(values.max())
    if pd.api.types.is_numeric_dtype(values):
        return format_range_value(values.min()), format_range_value(values.max())
    if units in {"PST", "PST date"}:
        text = values.astype(str)
        return text.min(), text.max()
    return "N/A", "N/A"


def prepare_data_dictionary(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for table_name, table in tables.items():
        definitions = FIELD_METADATA[table_name]
        if set(table.columns) != set(definitions):
            missing = sorted(set(table.columns) - set(definitions))
            extra = sorted(set(definitions) - set(table.columns))
            raise ValueError(
                f"Data dictionary mismatch for {table_name}. Missing definitions: {missing}. "
                f"Extra definitions: {extra}."
            )
        for field_name in table.columns:
            description, units = definitions[field_name]
            minimum, maximum = field_range(table[field_name], units)
            rows.append(
                {
                    "Table Name": table_name,
                    "Field Name": field_name,
                    "Description": description,
                    "Units": units,
                    "Min": minimum,
                    "Max": maximum,
                }
            )
    return pd.DataFrame(rows)


def main() -> int:
    args = parse_args()
    deployments = prepare_deployments(args.data_dir / "deployments.csv")
    classifications = prepare_classifications(args.data_dir / "deployments", deployments)
    temperature = prepare_temperature(args.data_dir / "temperature_data_2023.csv")
    wind = prepare_wind(args.data_dir / "wind", deployments)
    analysis_30_minute = prepare_analysis_30_minute(
        args.data_dir / "monarch_analysis_lag30min.csv"
    )
    analysis_next_day = prepare_analysis_next_day(
        args.data_dir / "monarch_daily_lag_analysis_nextday_window.csv"
    )
    tables = {
        "deployments": deployments,
        "classifications": classifications,
        "temperature_measurements": temperature,
        "wind_measurements": wind,
        "analysis_30_minute": analysis_30_minute,
        "analysis_next_day": analysis_next_day,
    }
    data_dictionary = prepare_data_dictionary(tables)

    for table_name, table in tables.items():
        write_csv(table, args.output_dir / f"{table_name}.csv")
    write_csv(data_dictionary, args.output_dir / "data_dictionary.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
