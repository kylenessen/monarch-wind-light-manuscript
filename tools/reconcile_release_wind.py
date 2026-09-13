# /// script
# requires-python = ">=3.13"
# dependencies = ["pandas>=2.3"]
# ///
"""Merge source wind databases and retain sensor records inside study intervals."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3

import pandas as pd


MEASUREMENTS = ["wind_speed_m_s", "wind_gust_m_s", "wind_direction_degrees"]
IDENTITY = ["wind_sensor_name", "timestamp_recorded", *MEASUREMENTS]
ALIASES = {"oc sw catfable": "CatFable"}


def read_only(path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def get_intervals(deployments_gpkg, cameras_gpkg, photo_intervals):
    with read_only(deployments_gpkg) as db:
        first = pd.read_sql_query('SELECT deployment_id,camera_name,wind_meter_name,Deployed_time,Recovered_time,notes FROM deployments', db)
    with read_only(cameras_gpkg) as db:
        second = pd.read_sql_query('SELECT deployment_ID,ID,wind_meter_ID,Notes FROM cameras', db)
    photos = pd.read_csv(photo_intervals, keep_default_na=False)
    if photos["deployment_key"].duplicated().any():
        raise ValueError("Repeated photo interval key")
    if set(photos.deployment_id) != set(second.deployment_ID):
        raise ValueError("Camera metadata and photo intervals do not match")
    records = []
    for r in first.itertuples(index=False):
        sensor = "" if r.wind_meter_name in (None, "NA", "") else r.wind_meter_name
        records.append({"season": "2023-2024", "deployment_id": r.deployment_id,
                        "camera_name": r.camera_name, "wind_sensor_name": sensor,
                        "start_time_recorded": r.Deployed_time, "end_time_recorded": r.Recovered_time,
                        "boundary_basis": "first_season_deployment_geopackage",
                        "photo_count_for_interval": "", "notes": r.notes or ""})
    by_id = photos.set_index("deployment_id")
    for r in second.itertuples(index=False):
        p = by_id.loc[r.deployment_ID]
        records.append({"season": "2024-2025", "deployment_id": r.deployment_ID,
                        "camera_name": r.ID, "wind_sensor_name": r.wind_meter_ID,
                        "start_time_recorded": p.start_time_recorded,
                        "end_time_recorded": p.end_time_recorded,
                        "boundary_basis": p.boundary_basis,
                        "photo_count_for_interval": p.photo_count_for_interval, "notes": r.Notes or ""})
    result = pd.DataFrame(records)
    # Case spelling is not a distinct instrument identity.
    result["wind_sensor_name"] = result["wind_sensor_name"].replace({"Stardust": "StarDust"})
    result.insert(0, "deployment_key", result.season + "/" + result.deployment_id)
    result["_start"] = pd.to_datetime(result.start_time_recorded, format="mixed", errors="coerce")
    result["_end"] = pd.to_datetime(result.end_time_recorded, format="mixed", errors="coerce")
    for r in result.itertuples(index=False):
        if r.start_time_recorded and pd.isna(pd.to_datetime(r.start_time_recorded)):
            raise ValueError(f"Invalid interval for {r.deployment_key}")
    valid = result._start.notna() & result._end.notna()
    if ((result.loc[valid, "_start"] > result.loc[valid, "_end"])).any():
        raise ValueError("Reversed interval")
    if result.deployment_key.duplicated().any():
        raise ValueError("Deployment keys are not unique")
    return result


def assign_sensor(stem, canonical):
    if stem.casefold() in canonical:
        return canonical[stem.casefold()], "exact_case_insensitive_filename"
    if stem.casefold() in ALIASES:
        return ALIASES[stem.casefold()], "explicit_filename_alias"
    return "", "not_a_study_sensor_filename"


def normalize(frame):
    frame = frame.copy()
    frame["_time"] = pd.to_datetime(frame.timestamp_recorded, format="mixed", errors="coerce")
    if frame._time.isna().any():
        raise ValueError("Matched wind rows include an invalid timestamp")
    if getattr(frame._time.dt, "tz", None) is not None:
        raise ValueError("Timezone-aware wind timestamps require explicit handling")
    for col in MEASUREMENTS:
        frame[col] = pd.to_numeric(frame[col].astype("string").str.strip(), errors="raise").astype(float)
        frame.loc[frame[col].eq(0), col] = 0.0
    frame["timestamp_recorded"] = frame._time.map(lambda t: t.isoformat())
    return frame


def measurement_id(row):
    values = [None if pd.isna(v) else v for v in row]
    return "wind_" + hashlib.sha256(json.dumps(values, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def deduplicate(frame):
    unique = frame.drop_duplicates(IDENTITY).copy()
    unique["measurement_id"] = [measurement_id(row) for row in unique[IDENTITY].itertuples(index=False, name=None)]
    if unique.measurement_id.duplicated().any():
        raise ValueError("Measurement identity collision")
    links = frame.merge(unique[[*IDENTITY, "measurement_id"]], on=IDENTITY, validate="many_to_one")
    counts = links.groupby("measurement_id").size()
    unique["source_record_count"] = unique.measurement_id.map(counts)
    unique["timestamp_conflict"] = unique.duplicated(["wind_sensor_name", "timestamp_recorded"], keep=False)
    return unique, links


def interval_matches(frame, start, end):
    return frame._time.between(start, end, inclusive="both")


def reconcile(repo, raw, photos, deployments_gpkg, cameras_gpkg, output):
    output.mkdir(parents=True, exist_ok=True)
    intervals = get_intervals(deployments_gpkg, cameras_gpkg, photos)
    canonical = {s.casefold(): s for s in intervals.wind_sensor_name if s}
    paths = [("repository/" + str(p.relative_to(repo)), p) for p in sorted((repo / "data/wind").glob("*.s3db"))]
    paths += [("portable/raw/" + str(p.relative_to(raw)), p) for p in sorted(raw.rglob("*.s3db"))]
    if not paths:
        raise ValueError("No source databases found")
    inventory, frames = [], []
    for i, (source, path) in enumerate(paths, 1):
        before = path.stat()
        sensor, match_basis = assign_sensor(path.stem, canonical)
        with read_only(path) as db:
            total, first, last = db.execute('SELECT count(*), min(time), max(time) FROM Wind').fetchone()
            units = db.execute('SELECT Units FROM Units').fetchall()
            log_interval = db.execute('SELECT LogInt FROM LogInt').fetchall()
            windows = intervals.loc[intervals.wind_sensor_name.eq(sensor) & intervals._start.notna() & intervals._end.notna()] if sensor else intervals.iloc[:0]
            matched = pd.DataFrame()
            # Datetime comparison happens in pandas to preserve fractional interval
            # boundaries and to handle ISO T and space timestamp representations.
            if len(windows):
                if units != [(2,)]:
                    raise ValueError(f"Unexpected units for study sensor {source}: {units}")
                frame = pd.read_sql_query('SELECT rowid AS source_rowid,id AS source_record_id,time AS timestamp_recorded,speed AS wind_speed_m_s,gust AS wind_gust_m_s,direction AS wind_direction_degrees FROM Wind', db)
                frame["_time"] = pd.to_datetime(frame.timestamp_recorded, format="mixed", errors="coerce")
                selected = pd.Series(False, index=frame.index)
                for _, w in windows.iterrows():
                    selected |= interval_matches(frame, w._start, w._end)
                matched = normalize(frame.loc[selected])
                matched["wind_sensor_name"] = sensor
                matched["source_database"] = source
                frames.append(matched)
        checksum = digest(path)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError(f"Database changed while reading: {source}")
        inventory.append({"source_database": source, "sha256": checksum,
                          "size_bytes": before.st_size, "wind_sensor_name": sensor,
                          "sensor_match_basis": match_basis, "source_rows": total,
                          "matched_source_rows": len(matched), "excluded_source_rows": total - len(matched),
                          "first_timestamp_raw": first, "last_timestamp_raw": last,
                          "units_table": json.dumps(units), "log_interval_table": json.dumps(log_interval)})
        if i % 10 == 0:
            print(f"Inventoried {i}/{len(paths)} databases", flush=True)
    if not frames or sum(len(f) for f in frames) == 0:
        raise ValueError("No wind records matched the study intervals")
    matched = pd.concat(frames, ignore_index=True)
    unique, links = deduplicate(matched)
    associations, reports = [], []
    for _, w in intervals.iterrows():
        if not w.wind_sensor_name:
            status, subset = "no_assigned_sensor", unique.iloc[:0]
        elif pd.isna(w._start) or pd.isna(w._end):
            status, subset = "no_photo_interval", unique.iloc[:0]
        else:
            subset = unique.loc[unique.wind_sensor_name.eq(w.wind_sensor_name) & interval_matches(unique, w._start, w._end)].copy()
            available = any(s["wind_sensor_name"] == w.wind_sensor_name for s in inventory)
            status = "records_available" if len(subset) else "no_records_in_interval" if available else "no_matching_sensor_database"
        if len(subset):
            subset = subset[["measurement_id", *IDENTITY, "source_record_count", "timestamp_conflict"]].copy()
            subset.insert(0, "deployment_id", w.deployment_id)
            subset.insert(0, "season", w.season)
            subset.insert(0, "deployment_key", w.deployment_key)
            subset["sensor_quality_note"] = "Source deployment notes report corrupted wind data" if w.deployment_key == "2023-2024/UDMH1" else ""
            associations.append(subset)
        reports.append({**{k: w[k] for k in intervals.columns if not k.startswith("_")},
                        "wind_status": status, "wind_record_count": len(subset),
                        "first_wind_timestamp": subset.timestamp_recorded.min() if len(subset) else "",
                        "last_wind_timestamp": subset.timestamp_recorded.max() if len(subset) else "",
                        "conflicting_timestamp_record_count": int(subset.timestamp_conflict.sum()) if len(subset) else 0})
    wind = pd.concat(associations, ignore_index=True).sort_values(["deployment_key", "timestamp_recorded", "measurement_id"])
    if wind.duplicated(["deployment_key", "measurement_id"]).any():
        raise ValueError("Duplicate deployment-measurement association")
    if set(wind.measurement_id) != set(unique.measurement_id):
        raise ValueError("Unassigned measurements survived filtering")
    inv = pd.DataFrame(inventory)
    if int(inv.matched_source_rows.sum()) != len(matched):
        raise ValueError("Source accounting failed")
    wind.to_csv(output / "wind_measurements.csv", index=False)
    links[["measurement_id", "source_database", "source_rowid", "source_record_id"]].sort_values(["measurement_id", "source_database", "source_rowid"]).to_csv(output / "wind_record_sources.csv", index=False)
    inv.to_csv(output / "wind_source_inventory.csv", index=False)
    pd.DataFrame(reports).to_csv(output / "deployment_wind_coverage.csv", index=False)
    intervals.drop(columns=["_start", "_end"]).to_csv(output / "deployment_intervals.csv", index=False)
    wind.loc[wind.timestamp_conflict].to_csv(output / "wind_timestamp_conflicts.csv", index=False)
    provenance = {"source_roots": {"repository": str(repo), "portable/raw": str(raw)},
                  "interval_sources": {str(p): digest(p) for p in [photos, deployments_gpkg, cameras_gpkg]},
                  "filename_aliases": ALIASES,
                  "interval_rule": "Assigned sensor and inclusive recorded-time bounds. No clock correction.",
                  "first_season_rule": "Full source deployment GeoPackage boundaries, preserving fractional seconds.",
                  "second_season_rule": "Earliest and latest current EXIF times among user-reviewed retained JPEGs.",
                  "duplicate_key": IDENTITY,
                  "units": "Numeric values retained in the existing manuscript release convention of m/s and degrees. All matched databases have Units=2.",
                  "counts": {"databases": len(inv), "source_rows": int(inv.source_rows.sum()),
                             "excluded_source_rows": int(inv.excluded_source_rows.sum()),
                             "matched_source_rows": len(matched), "exact_duplicate_copies_removed": len(matched) - len(unique),
                             "unique_measurements": len(unique), "deployment_measurement_rows": len(wind),
                             "shared_measurement_extra_associations": len(wind) - len(unique),
                             "conflicting_unique_measurements": int(unique.timestamp_conflict.sum())}}
    (output / "wind_summary.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(provenance["counts"], indent=2), flush=True)
    print(pd.DataFrame(reports)[["deployment_key", "wind_status", "wind_record_count"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--photo-intervals", type=Path, required=True)
    parser.add_argument("--deployments-gpkg", type=Path, required=True)
    parser.add_argument("--cameras-gpkg", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reconcile(args.repo.resolve(), args.raw.resolve(), args.photo_intervals.resolve(),
              args.deployments_gpkg.resolve(), args.cameras_gpkg.resolve(), args.output.resolve())
