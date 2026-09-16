"""Reconstruct TGR1 image metadata from its recorded deployment endpoints.

Run with uv run --no-project tools/prepare_tgr1_photos.py. ExifTool must be installed.
Corrected copies are written on MonarchSSD. Original photographs remain in raw/.
"""

import argparse
import csv
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
NOTE = (
    "TGR1 capture times were reconstructed from deployment start and end times. "
    "The visible timestamp overlay retains the incorrect camera date and time."
)


def reconstruct_times(recorded, start, end):
    """Align elapsed camera time to both anchors, preserving gaps in the sequence."""
    if len(recorded) < 2 or end <= start:
        raise ValueError("Two or more photographs and increasing deployment anchors are required")
    elapsed = [timedelta()]
    for previous, current in zip(recorded, recorded[1:]):
        interval = current - previous
        if interval < timedelta():
            # Observed TGR1 calendar jump. Its time of day continues by ten minutes.
            interval += timedelta(days=31)
            if not timedelta(seconds=598) <= interval <= timedelta(seconds=602):
                raise ValueError("Unexpected camera clock jump")
        if interval <= timedelta():
            raise ValueError("Camera times must advance in numbered photo order")
        elapsed.append(elapsed[-1] + interval)
    duration_ms = round((end - start).total_seconds() * 1000)
    return [start + timedelta(milliseconds=round(duration_ms * (value / elapsed[-1])))
            for value in elapsed]


def prepare(archive):
    source = archive / "raw/Unusual Deployments/TGR1/20240105/DCIM"
    destination = archive / "corrected_photos/TGR1"
    mapping_path = ROOT / "data/release_working/tgr1_photo_times.csv"
    inventory = json.loads(subprocess.check_output([
        "exiftool", "-r", "-ext", "JPG", "-json", "-DateTimeOriginal", str(source)
    ], text=True))
    inventory.sort(key=lambda row: row["SourceFile"])
    if len(inventory) != 2973:
        raise ValueError("The TGR1 source collection has changed. Review it before reconstruction.")
    with (archive / "reconciled_2026-09-13/deployment_intervals.csv").open(newline="") as handle:
        deployment = next(row for row in csv.DictReader(handle)
                          if row["deployment_key"] == "2023-2024/TGR1")
    start = datetime.fromisoformat(deployment["start_time_recorded"])
    end = datetime.fromisoformat(deployment["end_time_recorded"])
    recorded = [datetime.strptime(row["DateTimeOriginal"], "%Y:%m:%d %H:%M:%S")
                for row in inventory]
    corrected = reconstruct_times(recorded, start, end)
    mapping = [dict(
        source_relative_path=str(Path(row["SourceFile"]).relative_to(archive)),
        original_timestamp_recorded=original.isoformat(),
        timestamp_recorded=timestamp.isoformat(timespec="milliseconds"),
        image_filename="TGR1_" + timestamp.strftime("%Y%m%d%H%M%S") + ".JPG",
    ) for row, original, timestamp in zip(inventory, recorded, corrected)]
    expected = {row["image_filename"] for row in mapping}
    if len(expected) != len(mapping):
        raise ValueError("Reconstructed filenames must be unique")
    if destination.is_symlink():
        raise ValueError("Corrected copies must use a separate directory")
    if destination.exists() and any(destination.iterdir()):
        if not mapping_path.is_file():
            raise ValueError("Existing output directory has no reconstruction mapping")
        with mapping_path.open(newline="") as handle:
            if list(csv.DictReader(handle)) != mapping:
                raise ValueError("Existing reconstruction uses different source records or anchors")
        if not {path.name for path in destination.iterdir()} <= expected | {".DS_Store"}:
            raise ValueError("Unexpected files in corrected photo directory")
    destination.mkdir(parents=True, exist_ok=True)
    with mapping_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(mapping[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(mapping)
    with tempfile.TemporaryDirectory(prefix="monarch-tgr1-") as temporary:
        metadata_csv = Path(temporary) / "metadata.csv"
        paths_file = Path(temporary) / "paths.txt"
        tags = []
        for row, timestamp in zip(mapping, corrected):
            target = destination / row["image_filename"]
            original = archive / row["source_relative_path"]
            if target.is_symlink() or (target.exists() and target.samefile(original)):
                raise ValueError("Corrected photographs cannot link to the raw source")
            shutil.copy2(original, target)
            value = timestamp.strftime("%Y:%m:%d %H:%M:%S")
            fraction = f"{timestamp.microsecond // 1000:03d}"
            tags.append({"SourceFile": str(target), "EXIF:DateTimeOriginal": value,
                         "EXIF:CreateDate": value, "EXIF:ModifyDate": value,
                         "EXIF:SubSecTimeOriginal": fraction,
                         "EXIF:SubSecTimeDigitized": fraction, "EXIF:SubSecTime": fraction,
                         "EXIF:ImageDescription": NOTE})
        with metadata_csv.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(tags[0]))
            writer.writeheader()
            writer.writerows(tags)
        paths_file.write_text("\n".join(row["SourceFile"] for row in tags) + "\n")
        subprocess.run(["exiftool", "-overwrite_original", "-P",
                        "-csv=" + str(metadata_csv), "-@", str(paths_file)], check=True)
    print(json.dumps(dict(photos=len(mapping), first=mapping[0]["timestamp_recorded"],
                          last=mapping[-1]["timestamp_recorded"], output=str(destination)), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("/Volumes/MonarchSSD/data_release"))
    prepare(parser.parse_args().archive)
