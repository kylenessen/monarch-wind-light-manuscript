# /// script
# requires-python = ">=3.13"
# dependencies = ["pillow>=11,<13"]
# ///
"""Create a separate, resumable photograph export without modifying source files."""

import argparse
import csv
from contextlib import closing
import ctypes
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid

from PIL import Image


def clone_file(source, target):
    """APFS copy-on-write clone. This creates a separate inode, not a hard link."""
    if sys.platform != "darwin":
        raise OSError("APFS cloning requires macOS")
    libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    function = libc.clonefile
    function.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint32]
    function.restype = ctypes.c_int
    if function(os.fsencode(source), os.fsencode(target), 1) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))


def choose_copy_method(source, parent):
    if sys.platform == "darwin" and source.stat().st_dev == parent.stat().st_dev:
        with tempfile.TemporaryDirectory(prefix=".clone-probe-", dir=parent) as directory:
            original = Path(directory) / "original"
            duplicate = Path(directory) / "duplicate"
            original.write_bytes(b"clone probe")
            try:
                clone_file(original, duplicate)
                if duplicate.read_bytes() != original.read_bytes():
                    raise ValueError("Clone probe content mismatch")
                duplicate.write_bytes(b"independent edit")
                if original.read_bytes() != b"clone probe":
                    raise ValueError("Clone probe is not independent")
                return "clone"
            except OSError:
                pass
    return "copy"


def write_status(destination, phase, **details):
    target = destination.with_name(destination.name + ".status.json")
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps({"phase": phase, "pid": os.getpid(),
                                    "updated": datetime.now().astimezone().isoformat(),
                                    **details}, indent=2) + "\n")
    temporary.replace(target)


def connect(destination):
    db = sqlite3.connect(destination / "metadata" / "inventory.sqlite")
    db.row_factory = sqlite3.Row
    return db


def plan(source, geopackage, destination):
    source = source.resolve(strict=True)
    destination = destination.resolve()
    if destination == source or source in destination.parents:
        raise ValueError("The export must be outside the source folder")
    resuming = destination.exists()
    if resuming and not (destination / "metadata" / "inventory.sqlite").is_file():
        raise FileExistsError(f"Destination is not a recognized export {destination}")
    if resuming:
        geopackage = destination / "metadata" / "cameras.gpkg"
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
    if not resuming:
        (destination / "metadata").mkdir(parents=True)
        snapshot = sqlite3.connect(destination / "metadata" / "cameras.gpkg")
        upstream.backup(snapshot)
        snapshot.close()
    upstream.rollback()
    upstream.close()
    with closing(connect(destination)) as db:
        db.execute("CREATE TABLE IF NOT EXISTS settings (source TEXT NOT NULL, copy_method TEXT NOT NULL, plan_complete INTEGER NOT NULL DEFAULT 0)")
        if not resuming:
            method = choose_copy_method(source, destination.parent)
            db.execute("INSERT INTO settings (source,copy_method) VALUES (?,?)", (str(source), method))
        settings = db.execute("SELECT * FROM settings").fetchone()
        if settings is None or settings["source"] != str(source):
            raise ValueError("The source folder does not match this export's inventory")
        method = settings["copy_method"] if "copy_method" in settings.keys() else "copy"
        db.execute("""CREATE TABLE IF NOT EXISTS files (
            source_relative TEXT PRIMARY KEY, camera TEXT NOT NULL,
            deployment TEXT NOT NULL, destination_relative TEXT NOT NULL,
            size INTEGER NOT NULL, source_mtime_ns INTEGER NOT NULL,
            capture_time TEXT, note TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
            sha256 TEXT, error TEXT)""")
        db.commit()
        print(f"Copy method {method}", flush=True)
        n = 0
        for camera, deployment in mapping.items():
            (destination / deployment).mkdir(exist_ok=True)
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
                    existing = db.execute("SELECT * FROM files WHERE source_relative=?", (str(relative),)).fetchone()
                    if existing is not None:
                        check_source(path, existing)
                        n += 1
                        continue
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
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS destination_unique ON files(destination_relative)")
        db.commit()
        total = db.execute("SELECT coalesce(sum(size),0) FROM files").fetchone()[0]
        required = (0 if method == "clone" else total) + 1024**3
        if shutil.disk_usage(destination).free < required:
            raise ValueError("Not enough free space for the export")
        with (destination / "metadata" / "deployment_mapping.csv").open("w", newline="") as handle:
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
            f"Copy method is {method}. APFS clones are independent files that initially share storage.\n"
            "metadata/manifest.csv links the exported files to their original paths and records SHA-256 checksums.\n"
            "metadata/cameras.gpkg is a snapshot of the camera records used for this export.\n"
            "Deployment IDs may overlap the first season. Keep this archive separate until IDs are reconciled.\n"
            f"\nOriginal source folder\n{source}\n"
        )
        export_manifest(db, destination)
        if "plan_complete" in settings.keys():
            db.execute("UPDATE settings SET plan_complete=1")
            db.commit()
        print(f"Plan complete. {n:,} files, {total / 1024**3:.2f} GiB", flush=True)


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
    with closing(connect(destination)) as db:
        settings = db.execute("SELECT * FROM settings").fetchone()
        source = Path(settings["source"])
        method = settings["copy_method"] if "copy_method" in settings.keys() else "copy"
        if "plan_complete" in settings.keys() and not settings["plan_complete"]:
            raise ValueError("Inventory is incomplete. Use the run command to resume planning first")
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
                    if method == "clone":
                        clone_file(original, temporary)
                        checksum = digest(original)
                    else:
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
            except KeyboardInterrupt:
                db.commit()
                raise
            finally:
                if temporary is not None and temporary.exists():
                    temporary.unlink()
            count += 1
            if count % 100 == 0:
                db.commit()
            if count % 1000 == 0:
                print(f"Processed {count:,} files, {copied_bytes / 1024**3:.2f} GiB this run, {time.monotonic() - started:.0f} seconds", flush=True)
                write_status(destination, "copying", counts=dict(db.execute("SELECT status,count(*) FROM files GROUP BY status")))
        db.commit()
        export_manifest(db, destination)
        status = dict(db.execute("SELECT status,count(*) FROM files GROUP BY status"))
        (destination / "metadata" / "copy_status.json").write_text(json.dumps(status, indent=2) + "\n")
        print(json.dumps(status), flush=True)
        if status.get("error"):
            raise RuntimeError(f"{status['error']} files need attention. See metadata/manifest.csv")
        return status


def run_export(source, geopackage, destination):
    source = source.resolve(strict=True)
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock_path = destination.with_name(destination.name + ".lock")
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("An export process is already running for this destination")
        try:
            complete = False
            if (destination / "metadata" / "inventory.sqlite").is_file():
                with closing(connect(destination)) as db:
                    settings = db.execute("SELECT * FROM settings").fetchone()
                    if settings["source"] != str(source):
                        raise ValueError("The source folder does not match this export's inventory")
                    complete = bool(settings["plan_complete"]) if "plan_complete" in settings.keys() else (destination / "metadata" / "manifest.csv").is_file()
            if not complete:
                write_status(destination, "inventory")
                plan(source, geopackage, destination)
            write_status(destination, "copying")
            result = copy_files(destination)
            write_status(destination, "completed", counts=result)
            print("Export complete", flush=True)
        except BaseException as error:
            write_status(destination, "interrupted" if isinstance(error, KeyboardInterrupt) else "failed", error=str(error))
            raise


def launch_background(source, geopackage, destination):
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-u", str(Path(__file__).resolve()), "run",
               str(source.resolve(strict=True)), str(geopackage.resolve(strict=True)), str(destination)]
    if sys.platform == "darwin":
        command = ["/usr/bin/caffeinate", "-i", *command]
    log_path = destination.with_name(destination.name + ".log")
    with log_path.open("a") as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)
    print(f"Started unattended export. PID {process.pid}\nLog {log_path}", flush=True)


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
    running = sub.add_parser("run", help="Inventory and copy in one command, or resume an interrupted export")
    running.add_argument("source", type=Path)
    running.add_argument("geopackage", type=Path)
    running.add_argument("destination", type=Path)
    running.add_argument("--background", action="store_true", help="Detach the job and save its log and status beside the export")
    args = parser.parse_args()
    if args.action == "plan":
        plan(args.source, args.geopackage, args.destination)
    elif args.action == "copy":
        copy_files(args.destination, args.limit)
    elif args.background:
        launch_background(args.source, args.geopackage, args.destination)
    else:
        run_export(args.source, args.geopackage, args.destination)
