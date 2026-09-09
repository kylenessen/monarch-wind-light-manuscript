"""Create a separate, resumable photograph export without modifying source files."""

import argparse
import csv
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import time
import uuid

from PIL import Image


def connect(destination):
    db = sqlite3.connect(destination / "metadata" / "inventory.sqlite")
    db.row_factory = sqlite3.Row
    return db


def plan(source, geopackage, destination):
    source = source.resolve(strict=True)
    destination = destination.resolve()
    if destination == source or source in destination.parents:
        raise ValueError("The export must be outside the source folder")
    if destination.exists():
        raise FileExistsError(destination)
    upstream = sqlite3.connect(geopackage.resolve().as_uri() + "?mode=ro", uri=True)
    upstream.execute("BEGIN")
    mapping = dict(upstream.execute("SELECT ID, deployment_ID FROM cameras"))
    for camera, deployment in mapping.items():
        if not camera or not deployment or deployment != deployment.strip():
            raise ValueError("Every camera needs a nonblank deployment ID")
        if any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in deployment):
            raise ValueError(f"Unsafe deployment ID {deployment!r}")
    if len(mapping) != upstream.execute("SELECT count(*) FROM cameras").fetchone()[0]:
        raise ValueError("Duplicate camera IDs")
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("Duplicate deployment IDs within this season")
    unknown = {p.name for p in source.iterdir() if p.is_dir() and not p.name.startswith(".")} - mapping.keys()
    if unknown:
        raise ValueError(f"Camera folders without deployment IDs {unknown}")
    (destination / "metadata").mkdir(parents=True)
    snapshot = sqlite3.connect(destination / "metadata" / "cameras.gpkg")
    upstream.backup(snapshot)
    snapshot.close()
    upstream.rollback()
    upstream.close()
    db = connect(destination)
    db.execute("CREATE TABLE settings (source TEXT NOT NULL)")
    db.execute("INSERT INTO settings VALUES (?)", (str(source),))
    db.execute("""CREATE TABLE files (
        source_relative TEXT PRIMARY KEY, camera TEXT NOT NULL,
        deployment TEXT NOT NULL, destination_relative TEXT NOT NULL,
        size INTEGER NOT NULL, source_mtime_ns INTEGER NOT NULL,
        capture_time TEXT, note TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
        sha256 TEXT, error TEXT)""")
    n = 0
    for camera, deployment in mapping.items():
        (destination / deployment).mkdir()
        for directory, dirs, names in os.walk(source / camera, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith("."))
            for name in sorted(names):
                if name.startswith("."):
                    continue
                path = Path(directory) / name
                if path.is_symlink():
                    raise ValueError(f"Source symlink requires review {path}")
                stat = path.stat()
                relative = path.relative_to(source)
                within_camera = path.relative_to(source / camera)
                timestamp = None
                note = "original_non_jpeg"
                target = Path(deployment) / "other_media" / within_camera
                if path.suffix.lower() in {".jpg", ".jpeg"}:
                    try:
                        with Image.open(path) as image:
                            if image.format != "JPEG":
                                raise ValueError("File is not a JPEG")
                            raw = image.getexif().get_ifd(34665).get(36867)
                            if not isinstance(raw, str):
                                raise ValueError("Missing EXIF DateTimeOriginal")
                            timestamp = datetime.strptime(raw.strip().strip("\0"), "%Y:%m:%d %H:%M:%S")
                        target = Path(deployment) / f"{deployment}_{timestamp:%Y%m%d%H%M%S}.JPG"
                        note = "capture_time_used_without_correction"
                    except Exception as error:
                        target = Path(deployment) / "review_needed" / within_camera
                        note = f"unreadable_capture_time {type(error).__name__} {error}"
                db.execute("""INSERT INTO files
                    (source_relative,camera,deployment,destination_relative,size,
                     source_mtime_ns,capture_time,note) VALUES (?,?,?,?,?,?,?,?)""",
                    (str(relative),camera,deployment,str(target),stat.st_size,stat.st_mtime_ns,
                     timestamp.isoformat() if timestamp else None,note))
                n += 1
                if n % 10000 == 0:
                    db.commit()
                    print(f"Inventoried {n:,} files", flush=True)
    duplicates = db.execute("SELECT destination_relative FROM files GROUP BY destination_relative HAVING count(*) > 1").fetchall()
    for (target,) in duplicates:
        rows = db.execute("SELECT source_relative,deployment FROM files WHERE destination_relative=?", (target,)).fetchall()
        for row in rows:
            new_target = Path(row["deployment"]) / "review_needed" / Path(row["source_relative"]).relative_to(Path(row["source_relative"]).parts[0])
            db.execute("UPDATE files SET destination_relative=?,note='duplicate_capture_time' WHERE source_relative=?",
                       (str(new_target),row["source_relative"]))
    db.execute("CREATE UNIQUE INDEX destination_unique ON files(destination_relative)")
    db.commit()
    total = db.execute("SELECT coalesce(sum(size),0) FROM files").fetchone()[0]
    if shutil.disk_usage(destination).free < total + 1024**3:
        raise ValueError("Not enough free space for the export")
    with (destination / "metadata" / "deployment_mapping.csv").open("x", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["camera_id", "deployment_id", "file_count"])
        for camera, deployment in mapping.items():
            count = db.execute("SELECT count(*) FROM files WHERE camera=?", (camera,)).fetchone()[0]
            writer.writerow([camera, deployment, count])
    (destination / "README.txt").write_text(
        "Second-season review copy\n\n"
        "Each deployment uses the camera's assigned deployment_ID at export planning time.\n"
        "All nonhidden source files are included. No date filtering or deployment splitting was applied.\n"
        "JPEG names use EXIF DateTimeOriginal exactly as recorded, without timezone or clock corrections.\n"
        "Videos and other non-JPEG files retain their original paths under other_media.\n"
        "JPEGs with unreadable or duplicate timestamps retain their original paths under review_needed.\n"
        "All file contents are copied without image processing or metadata edits.\n"
        "metadata/manifest.csv links the exported files to their original paths and records SHA-256 checksums.\n"
        "metadata/cameras.gpkg is a snapshot of the camera records used for this export.\n"
        "Deployment IDs may overlap the first season. Keep this archive separate until IDs are reconciled.\n"
        f"\nOriginal source folder\n{source}\n"
    )
    export_manifest(db, destination)
    print(f"Plan complete. {n:,} files, {total / 1024**3:.2f} GiB", flush=True)
    db.close()


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def check_source(path, row):
    stat = path.stat()
    if path.is_symlink() or (stat.st_size, stat.st_mtime_ns) != (row["size"], row["source_mtime_ns"]):
        raise ValueError(f"Source changed since inventory {path}")


def export_manifest(db, destination):
    rows = db.execute("SELECT * FROM files ORDER BY camera,source_relative")
    temporary = destination / "metadata" / f".manifest-{uuid.uuid4().hex}.csv"
    with temporary.open("x", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([c[0] for c in rows.description])
        writer.writerows(rows)
    temporary.replace(destination / "metadata" / "manifest.csv")


def copy_files(destination, limit=None):
    destination = destination.resolve(strict=True)
    db = connect(destination)
    source = Path(db.execute("SELECT source FROM settings").fetchone()[0])
    started = time.monotonic()
    count = 0
    copied_bytes = 0
    for row in db.execute("SELECT * FROM files WHERE status != 'copied' ORDER BY camera,source_relative").fetchall():
        if limit is not None and count >= limit:
            break
        original = source / row["source_relative"]
        target = destination / row["destination_relative"]
        temporary = None
        try:
            check_source(original, row)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() or target.is_symlink():
                if target.is_symlink() or not target.is_file() or target.stat().st_size != row["size"]:
                    raise FileExistsError(f"Refusing to replace {target}")
                checksum = digest(original)
                if digest(target) != checksum:
                    raise FileExistsError(f"Existing destination differs from source {target}")
            else:
                temporary = target.parent / f".copy-{uuid.uuid4().hex}.partial"
                hasher = hashlib.sha256()
                with original.open("rb") as incoming, temporary.open("xb") as outgoing:
                    while block := incoming.read(1024 * 1024):
                        hasher.update(block)
                        outgoing.write(block)
                checksum = hasher.hexdigest()
                if temporary.stat().st_size != row["size"] or digest(temporary) != checksum:
                    raise ValueError(f"Copy verification failed {original}")
                check_source(original, row)
                shutil.copystat(original, temporary)
                # Linking our independent temporary copy publishes without overwriting anything.
                os.link(temporary, target)
                temporary.unlink()
                temporary = None
            check_source(original, row)
            db.execute("UPDATE files SET status='copied',sha256=?,error=NULL WHERE source_relative=?",
                       (checksum,row["source_relative"]))
            copied_bytes += row["size"]
        except Exception as error:
            db.execute("UPDATE files SET status='error',error=? WHERE source_relative=?",
                       (str(error),row["source_relative"]))
            print(f"ERROR {row['source_relative']} {error}", flush=True)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        count += 1
        if count % 100 == 0:
            db.commit()
        if count % 1000 == 0:
            print(f"Processed {count:,} files, {copied_bytes / 1024**3:.2f} GiB this run, {time.monotonic() - started:.0f} seconds", flush=True)
    db.commit()
    export_manifest(db, destination)
    status = dict(db.execute("SELECT status,count(*) FROM files GROUP BY status"))
    (destination / "metadata" / "copy_status.json").write_text(json.dumps(status, indent=2) + "\n")
    print(json.dumps(status), flush=True)
    db.close()
    if status.get("error"):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    planning = sub.add_parser("plan")
    planning.add_argument("source", type=Path)
    planning.add_argument("geopackage", type=Path)
    planning.add_argument("destination", type=Path)
    copying = sub.add_parser("copy")
    copying.add_argument("destination", type=Path)
    copying.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.action == "plan":
        plan(args.source, args.geopackage, args.destination)
    else:
        copy_files(args.destination, args.limit)
