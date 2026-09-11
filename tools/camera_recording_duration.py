# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Summarize observed camera recording spans from a photo export inventory."""

import argparse
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime
import json
from pathlib import Path
import sqlite3
from statistics import median


def summarize_camera(camera, deployment, rows, gap_hours):
    dated = sorted(datetime.fromisoformat(row["capture_time"])
                   for row in rows if row["capture_time"])
    timestamps = sorted(set(dated))
    segments = []
    gaps = []
    for stamp in timestamps:
        if segments:
            previous = segments[-1][-1]
            hours = (stamp - previous).total_seconds() / 3600
            if hours > gap_hours:
                gaps.append({"before": previous.isoformat(), "after": stamp.isoformat(),
                             "hours": hours})
                segments.append([])
        else:
            segments.append([])
        segments[-1].append(stamp)
    counts = Counter(dated)
    runs = []
    for segment in segments:
        intervals = [(b - a).total_seconds() for a, b in zip(segment, segment[1:])]
        runs.append({
            "first_photo": segment[0].isoformat(),
            "last_photo": segment[-1].isoformat(),
            "span_days": (segment[-1] - segment[0]).total_seconds() / 86400,
            "photo_count": sum(counts[t] for t in segment),
            "unique_timestamps": len(segment),
            "median_interval_seconds": median(intervals) if intervals else None,
            "largest_gap_hours": max(intervals) / 3600 if intervals else None,
        })
    main = max(runs, key=lambda r: (r["span_days"], r["photo_count"]), default=None)
    return {
        "camera": camera, "deployment": deployment,
        "file_count": len(rows), "timestamped_photo_count": len(dated),
        "files_without_photo_timestamp": len(rows) - len(dated),
        "duplicate_timestamp_extra_photos": len(dated) - len(timestamps),
        "export_status_counts": dict(Counter(row["status"] for row in rows)),
        "main_run": main, "runs": runs, "gaps_over_threshold": gaps,
        "photos_outside_main_run": len(dated) - main["photo_count"] if main else 0,
    }


def analyze(export, gap_hours=24):
    if not 0 < gap_hours < float("inf"):
        raise ValueError("Gap hours must be a finite positive number")
    inventory = export / "metadata" / "inventory.sqlite"
    cameras = export / "metadata" / "cameras.gpkg"
    grouped = defaultdict(list)
    with closing(sqlite3.connect(inventory.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        for row in db.execute("SELECT camera,deployment,capture_time,status FROM files"):
            grouped[(row["camera"], row["deployment"])].append(dict(row))
    # Include assigned cameras with no photos, using the export's frozen mapping.
    with closing(sqlite3.connect(cameras.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        for camera, deployment in db.execute("SELECT ID,deployment_ID FROM cameras"):
            grouped.setdefault((camera, deployment), [])
    return {
        "export": str(export.resolve()), "gap_threshold_hours": gap_hours,
        "method": "Split sorted unique EXIF photo timestamps at gaps greater than the threshold. "
                  "Report the longest elapsed segment as the main run and retain every other segment. "
                  "Durations are last photo minus first photo, with no clock or timezone correction. "
                  "These are observed recording spans, not measured battery lifetimes. "
                  "Videos and files without a photo timestamp do not contribute to duration. "
                  "The saved export inventory is used, so later manual edits are not reflected.",
        "cameras": [summarize_camera(camera, deployment, rows, gap_hours)
                    for (camera, deployment), rows in sorted(grouped.items())],
    }


def markdown(report):
    lines = ["# Camera recording duration", "", report["method"], "",
             f"Run boundary is a gap greater than {report['gap_threshold_hours']:g} hours. "
             "Smaller gaps remain inside the reported span. No source or export photos were changed.", "",
             "| Camera | Deployment | First main-run photo | Last main-run photo | Days | Photos in main run | Largest gap, hours |",
             "| --- | --- | --- | --- | ---: | ---: | ---: |"]
    for camera in report["cameras"]:
        run = camera["main_run"]
        if run:
            largest = run["largest_gap_hours"]
            gap = f"{largest:.2f}" if largest is not None else "N/A"
            lines.append(f"| {camera['camera']} | {camera['deployment']} | "
                         f"{run['first_photo'].replace('T', ' ')} | {run['last_photo'].replace('T', ' ')} | "
                         f"{run['span_days']:.2f} | {run['photo_count']:,} | {gap} |")
        else:
            lines.append(f"| {camera['camera']} | {camera['deployment']} | No dated photos | | | | |")
    lines += ["", "## Review notes", ""]
    for camera in report["cameras"]:
        notes = []
        if camera["photos_outside_main_run"]:
            other = [r for r in camera["runs"] if r is not camera["main_run"]]
            dates = ", ".join(f"{r['first_photo']} to {r['last_photo']} (photo count {r['photo_count']})" for r in other)
            notes.append(f"Photo count outside the main run is {camera['photos_outside_main_run']}. Additional segments are {dates}.")
        if camera["files_without_photo_timestamp"]:
            notes.append(f"The count of files without a photo capture timestamp is {camera['files_without_photo_timestamp']}, including any videos.")
        if camera["duplicate_timestamp_extra_photos"]:
            notes.append(f"{camera['duplicate_timestamp_extra_photos']} extra photos share a timestamp with another photo. They count as photos but add no elapsed time.")
        if not camera["file_count"]:
            notes.append("The assigned camera has no files in the inventory.")
        if any(status != "copied" for status in camera["export_status_counts"]):
            notes.append(f"Some export records are unfinished. Status counts are {camera['export_status_counts']}.")
        if notes:
            lines += [f"{camera['camera']} ({camera['deployment']}). " + " ".join(notes), ""]
    lines += ["The main spans cannot establish uninterrupted operation or battery life. "
              "Battery replacements, camera service, clock changes, missing files, and retrieval dates need field records. "
              "Shorter gaps are reported without assuming their cause.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path, help="Deployment export containing metadata/inventory.sqlite")
    parser.add_argument("--gap-hours", type=float, default=24,
                        help="Separate timestamp segments at larger gaps, default 24")
    parser.add_argument("--output", type=Path, required=True, help="Folder for duration_report.md and duration_report.json")
    args = parser.parse_args()
    report = analyze(args.export, args.gap_hours)
    rendered = markdown(report)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "duration_report.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output / "duration_report.md").write_text(rendered)
    print(rendered)


if __name__ == "__main__":
    main()
