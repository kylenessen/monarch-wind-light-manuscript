# /// script
# requires-python = ">=3.13"
# dependencies = ["Pillow>=11"]
# ///
"""Return reviewed JPEGs to deployment folders and inventory the cleaned set."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from datetime import datetime

from PIL import Image

EXCLUSION_FILE = Path(__file__).resolve().parents[1] / "data/release_working/deployment_exclusions.json"


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def capture_time(path):
    with Image.open(path) as im:
        if im.format != "JPEG":
            raise ValueError(f"Not a JPEG: {path}")
        value = im.getexif().get_ifd(34665).get(36867)
    return datetime.strptime(value.strip().strip("\0"), "%Y:%m:%d %H:%M:%S")


def write_csv(path, rows, fields):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def plan_moves(root, baseline):
    plan = []
    reserved = set()
    for path in sorted(root.glob("*/review_needed/**/*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.is_symlink() or path.suffix.lower() not in {".jpg", ".jpeg"}:
            raise ValueError(f"Unexpected review file: {path}")
        old = str(path.relative_to(root))
        if old not in baseline:
            raise ValueError(f"Review file missing from original inventory: {old}")
        deployment = path.relative_to(root).parts[0]
        timestamp = capture_time(path)
        stem = f"{deployment}_{timestamp:%Y%m%d%H%M%S}"
        target = root / deployment / (stem + ".JPG")
        occurrence = 1
        while target.exists() or str(target) in reserved:
            occurrence += 1
            target = root / deployment / f"{stem}_{occurrence:02d}.JPG"
        reserved.add(str(target))
        plan.append({"old_path": old, "new_path": str(target.relative_to(root)),
                     "sha256": digest(path), "capture_time": timestamp.isoformat(),
                     "occurrence": occurrence})
    return plan


def apply_moves(root, plan):
    # Hard-link then unlink on the same volume. Creating the link fails if the
    # destination exists. A crash between the two operations is resumable.
    for row in plan:
        old, new = root / row["old_path"], root / row["new_path"]
        if new.exists():
            if digest(new) != row["sha256"]:
                raise ValueError(f"Destination changed: {new}")
            if old.exists():
                if not os.path.samefile(old, new):
                    raise ValueError(f"Destination collision: {new}")
                old.unlink()
            continue
        if not old.exists() or digest(old) != row["sha256"]:
            raise ValueError(f"Review source changed: {old}")
        os.link(old, new)
        if digest(new) != row["sha256"]:
            raise ValueError(f"Move verification failed: {new}")
        old.unlink()


def run(root, output, exclusions):
    root = root.resolve()
    excluded_deployments = json.loads(EXCLUSION_FILE.read_text()) if EXCLUSION_FILE.exists() else {}
    output.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect((root / "metadata/inventory.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        baseline = {r["destination_relative"]: dict(r) for r in db.execute("SELECT * FROM files")}
    journal = output / "photo_rename_plan.json"
    if journal.exists():
        saved = json.loads(journal.read_text())
        if saved["root"] != str(root):
            raise ValueError("Rename journal belongs to a different export")
        plan = saved["moves"]
    else:
        plan = plan_moves(root, baseline)
        with journal.open("x") as handle:
            json.dump({"root": str(root), "moves": plan}, handle, indent=2)
    apply_moves(root, plan)
    renamed = {r["new_path"]: r for r in plan}
    originals = {r["old_path"]: r["new_path"] for r in plan}
    unknown_exclusions = set(exclusions)
    files, seen, photo_times = [], set(), {}
    for directory in sorted(root.iterdir()):
        if not directory.is_dir() or directory.name == "metadata" or directory.name.startswith("."):
            continue
        if f"2024-2025/{directory.name}" in excluded_deployments:
            if any(p.is_file() and not p.name.startswith(".") for p in directory.rglob("*")):
                raise ValueError(f"Excluded deployment now contains files and needs review: {directory.name}")
            continue
        photo_times[directory.name] = []
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or any(p.startswith(".") for p in path.relative_to(root).parts):
                continue
            if path.is_symlink():
                raise ValueError(f"Unexpected symlink: {path}")
            relative = str(path.relative_to(root))
            old = renamed[relative]["old_path"] if relative in renamed else relative
            if old not in baseline:
                raise ValueError(f"File missing from original inventory: {relative}")
            original = baseline[old]
            seen.add(old)
            stat = path.stat()
            same_stat = (stat.st_size, stat.st_mtime_ns) == (original["size"], original["source_mtime_ns"])
            checksum = renamed[relative]["sha256"] if relative in renamed else original["sha256"] if same_stat else digest(path)
            basis = "verified_during_rename" if relative in renamed else "export_hash_unchanged_size_mtime" if same_stat else "recomputed_after_review"
            timestamp = ""
            is_photo = path.suffix.lower() in {".jpg", ".jpeg"}
            if is_photo:
                timestamp = capture_time(path).isoformat()
            excluded = relative in exclusions
            unknown_exclusions.discard(relative)
            if is_photo and not excluded:
                photo_times[directory.name].append(timestamp)
            files.append({"season": "2024-2025", "deployment_id": directory.name,
                          "deployment_key": f"2024-2025/{directory.name}",
                          "relative_path": relative, "original_export_path": old,
                          "source_relative": original["source_relative"], "capture_time_recorded": timestamp,
                          "include_in_wind_interval": is_photo and not excluded,
                          "interval_exclusion_reason": exclusions.get(relative, ""),
                          "size_bytes": stat.st_size, "sha256": checksum, "checksum_basis": basis})
            if len(files) % 20000 == 0:
                print(f"Read current EXIF and inventoried {len(files):,} files", flush=True)
    if unknown_exclusions:
        raise ValueError(f"Exclusion paths not in cleaned set: {unknown_exclusions}")
    removed = [{"original_export_path": old, "source_relative": row["source_relative"],
                "deployment_id": row["deployment"], "reason": "absent_after_user_review"}
               for old, row in baseline.items() if old not in seen]
    intervals = [{"season": "2024-2025", "deployment_id": deployment,
                  "deployment_key": f"2024-2025/{deployment}",
                  "photo_count_for_interval": len(times),
                  "start_time_recorded": min(times) if times else "",
                  "end_time_recorded": max(times) if times else "",
                  "boundary_basis": "user_reviewed_photos" if times else "no_photos"}
                 for deployment, times in photo_times.items()]
    write_csv(output / "reviewed_image_manifest.csv", files, list(files[0]))
    write_csv(output / "removed_after_review.csv", removed,
              ["original_export_path", "source_relative", "deployment_id", "reason"])
    write_csv(output / "photo_intervals_2025.csv", intervals, list(intervals[0]))
    summary = {"renamed_review_files": len(plan), "retained_files": len(files),
               "excluded_deployments": excluded_deployments,
               "retained_photos": sum(bool(r["capture_time_recorded"]) for r in files),
               "absent_after_review": len(removed), "interval_exclusions": exclusions,
               "intervals": intervals}
    (output / "photo_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if len(files) + len(removed) != len(baseline):
        raise ValueError("Photo source accounting failed")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--exclude-times", type=Path, help="JSON mapping retained image paths to exclusion reasons")
    args = parser.parse_args()
    run(args.export, args.output, json.loads(args.exclude_times.read_text()) if args.exclude_times else {})
