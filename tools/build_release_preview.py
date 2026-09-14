"""Extract an unchanged, linked CSV and photo sample for USGS schema review.

Run with uv run --no-project tools/build_release_preview.py. All preview data
and the ZIP stay on the external drive. Source files are read only.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile


def read_csv(path):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def ten_rows(priority, candidates):
    chosen = []
    for row in priority + candidates:
        if row not in chosen:
            chosen.append(row)
        if len(chosen) == 10:
            return chosen
    raise ValueError("Insufficient distinct source rows for the preview")


def build(source, destination, replace=False):
    if destination.exists() and not replace:
        raise FileExistsError(f"Choose a new preview folder to preserve existing review files: {destination}")
    tables = {p.stem: read_csv(p) for p in sorted(source.glob("*.csv"))}
    rows = {name: data[1] for name, data in tables.items()}
    sc1 = [r["image_filename"] for r in rows["classifications"]
           if r["deployment_id"] == "SC1" and float(r["butterfly_index"]) > 0][:2]
    filenames = {
        *sc1,
        "SC12_20240129174001.JPG", "SC13_20241215120001.JPG",
        "CR01_20241103020001.JPG", "CR01_20241103021001.JPG",
    }
    selected = {
        "deployments": rows["deployments"],
        "data_dictionary": rows["data_dictionary"],
        "photo_index": [r for r in rows["photo_index"] if r["image_filename"] in filenames],
        "classifications": [r for r in rows["classifications"] if r["image_filename"] in filenames],
        "temperature_measurements": [r for r in rows["temperature_measurements"] if r["image_filename"] in filenames],
    }
    wind = rows["wind_measurements"]
    wind_examples = []
    for deployment, start in [("SC1", "2023-11-17T12:00"),
                              ("SC12", "2024-01-29T17:40"),
                              ("SC13", "2024-12-15T12:00"),
                              ("SC13", "2025-01-14")]:
        wind_examples.extend([r for r in wind if r["deployment_id"] == deployment
                              and r["timestamp"] >= start][:3])
    shared_time = next(r["timestamp"] for r in wind if r["deployment_id"] == "SC10")
    wind_examples.extend(r for r in wind if r["deployment_id"] in {"SC9", "SC10"}
                         and r["timestamp"] == shared_time)
    for direction in ("0", "360"):
        wind_examples.append(next(r for r in wind if float(r["wind_direction"] or -1) == int(direction)))
    fields = tables["wind_measurements"][0]
    unique = {tuple(r[f] for f in fields): r for r in wind_examples}
    selected["wind_measurements"] = sorted(unique.values(), key=lambda r: (r["deployment_id"], r["timestamp"]))

    wind_priority = []
    for deployment in ("SC1", "SC9", "SC10", "SC12", "SC13"):
        wind_priority.append(next(r for r in selected["wind_measurements"] if r["deployment_id"] == deployment))
    wind_priority.extend(next(r for r in selected["wind_measurements"] if float(r["wind_direction"]) == direction)
                         for direction in (0, 360))
    wind_priority.append(next(r for r in selected["wind_measurements"]
                              if r["deployment_id"] == "SC13" and r["timestamp"].startswith("2025-01-14")))
    selected["wind_measurements"] = ten_rows(wind_priority, selected["wind_measurements"])
    for name in ("classifications",):
        selected[name] = ten_rows(selected[name], rows[name])
    classified_names = {r["image_filename"] for r in selected["classifications"]}
    selected["temperature_measurements"] = [r for r in rows["temperature_measurements"] if r["image_filename"] in classified_names]
    selected["photo_index"] = ten_rows(selected["photo_index"],
                                      [r for r in rows["photo_index"] if r["image_filename"] in classified_names])

    assert set(selected) == set(tables)
    assert len(filenames) == 6
    assert all(len(chosen) == 10 for name, chosen in selected.items() if name not in {"deployments", "data_dictionary"})
    assert len({r["deployment_id"] for r in selected["deployments"]}) == len(selected["deployments"])
    photo_names = {r["image_filename"] for r in selected["photo_index"]}
    assert filenames <= photo_names
    assert {r["image_filename"] for r in selected["temperature_measurements"]} == classified_names
    definitions = {(r["table"], r["column"]) for r in selected["data_dictionary"]}
    assert all((name + ".csv", field) in definitions for name in selected if name != "data_dictionary" for field in tables[name][0])
    destination.mkdir(parents=True, exist_ok=replace)
    for name in ("analysis_30_minute.csv", "analysis_next_day.csv"):
        (destination / name).unlink(missing_ok=True)
    counts = {}
    for name, chosen in selected.items():
        fields, original = tables[name]
        original_values = {tuple(r[f] for f in fields) for r in original}
        assert all(tuple(r[f] for f in fields) in original_values for r in chosen)
        target = destination / f"{name}.csv"
        if name in {"deployments", "data_dictionary"}:
            shutil.copyfile(source / target.name, target)
        else:
            with target.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(chosen)
        saved_fields, saved_rows = read_csv(target)
        assert saved_fields == fields and saved_rows == chosen
        counts[name + ".csv"] = {"preview_rows": len(chosen), "full_release_rows": len(original), "columns": len(fields)}
    photo_checksums = {}
    for photo in selected["photo_index"]:
        if photo["image_filename"] not in filenames:
            continue
        relative = photo["relative_path"]
        original, target = source / relative, destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        assert not target.is_symlink() and digest(original) == digest(target)
        photo_checksums[relative] = digest(target)
        if replace:
            for old_season in ("2023-2024", "2024-2025"):
                legacy = destination / "photos" / old_season / photo["deployment_id"] / photo["image_filename"]
                if legacy.exists():
                    if digest(legacy) != photo_checksums[relative]:
                        raise ValueError(f"Old preview photo was modified {legacy}")
                    legacy.unlink()
                    if not any(legacy.parent.iterdir()):
                        legacy.parent.rmdir()
    for old_season in ("2023-2024", "2024-2025"):
        legacy = destination / "photos" / old_season
        if legacy.exists():
            legacy.rmdir()
    shutil.copyfile(source / "metadata.xml", destination / "metadata.xml")
    reference = destination / "full_release_reference"
    reference.mkdir(exist_ok=replace)
    shutil.copyfile(source / "README.md", reference / "README.md")
    annotations = destination / "classifications"
    annotations.mkdir(exist_ok=True)
    shutil.copyfile(source / "classifications/README.md", annotations / "README.md")
    for deployment in {r["deployment_id"] for r in selected["classifications"]}:
        shutil.copyfile(source / "classifications" / f"{deployment}.json",
                        annotations / f"{deployment}.json")

    header_text = "# CSV headers for USGS review\n\nHeaders are identical to the full draft release, in the same column order. "
    header_text += "The numbered lists below are for reading. Each CSV retains its standard comma-separated header row. "
    header_text += "Definitions, units and missing-value conventions are in data_dictionary.csv.\n"
    for name in tables:
        fields = tables[name][0]
        header_text += f"\n## {name}.csv\n\n{len(fields)} columns. {len(selected[name]):,} preview rows from {len(rows[name]):,} full-release rows.\n\n"
        header_text += "\n".join(f"{i}. `{field}`" for i, field in enumerate(fields, 1)) + "\n"
    (destination / "CSV_HEADERS.md").write_text(header_text)
    readme = """# Monarch data release preview for USGS review

Prepared for Zach on September 14, 2026.

This small preview supports review of file organization, CSV headers, column definitions and draft metadata before transfer of the full photo archive. Start with CSV_HEADERS.md for the column lists, then data_dictionary.csv for definitions, units and missing-value conventions. The CSV filenames and schemas match the full release. Sample rows retain the original values and formatting of their CSV fields.

This is a selected example set, not the complete dataset or a statistically representative sample. It is too small to reproduce the analyses. metadata.xml and full_release_reference/README.md describe the full draft release, including its full record counts and ranges. They have not been rewritten to describe this sample. The XML remains a draft with review placeholders.

## Included CSV files

| File | Preview rows | Full release rows | Columns |
| --- | ---: | ---: | ---: |
"""
    for name, count in counts.items():
        readme += f"| {name} | {count['preview_rows']:,} | {count['full_release_rows']:,} | {count['columns']} |\n"
    readme += """
deployments.csv and data_dictionary.csv are complete copies. Each of the other four CSVs contains exactly 10 selected data rows, plus its header. Dictionary minimum and maximum values describe the full release. Native JSON files for the sampled classified deployments are included in classifications/.

## Photo examples and table relationships

Six original JPEGs are included under photos/deployment_id/. All six are listed in the 10-row photo index. The other four index rows demonstrate the schema but their photos are not included. These are ordinary files, with no symbolic links. The images and their EXIF metadata have not been resized or edited.

The two SC1 photos have saved classifications. Their classification and temperature records are included, along with illustrative wind observations. Additional observation rows bring each sampled table to 10 rows. Those rows and the full deployment JSON files can reference photos available only in the complete release.

The first-season SC12 image and second-season SC13 image show distinct camera deployments. SC12 is NOVA with BlueLake. SC13 is IRIS with RockWall. Deployment identifiers are unique across the release. The two CR01 images show consecutive ten-minute observations.

The wind examples include both seasons, shared StarDust observations for SC9 and SC10, late zero-speed SC13 observations, and directions 0 and 360. They illustrate recorded values and documentation needs. The README and dictionary explain their limitations. No second-season classification or temperature records are included because those datasets cover the first season only.

Filenames use deployment_id_YYYYMMDDHHMMSS.JPG. Recorded device times have no newly applied daylight saving or UTC correction. Photo color and infrared appearance, overlays and timestamps in these examples are preserved as recorded.

## Review focus

Please assess the table organization, terminology, units, missing-value definitions, deployment joins and photo naming convention. The full dictionary defines each retained data column. The draft XML includes the clock caveat, source processing and coverage limitations, and identifies the administrative fields that still need USGS input.

The coauthor Word guide is being reviewed separately and is not included in this preview. Analysis scripts remain in the manuscript repository at https://github.com/kylenessen/monarch-wind-light-manuscript.
"""
    readme += "\n## Included photo paths\n\n```text\n" + "\n".join(sorted(photo_checksums)) + "\n```\n"
    (destination / "README.md").write_text(readme)
    archive = destination.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w" if replace else "x", compression=zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                zipped.write(path, destination.name + "/" + str(path.relative_to(destination)))
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        for path in destination.rglob("*"):
            if path.is_file():
                assert zipped.read(destination.name + "/" + str(path.relative_to(destination))) == path.read_bytes()
    return {"preview_folder": str(destination), "zip": str(archive), "zip_bytes": archive.stat().st_size,
            "files": sum(p.is_file() for p in destination.rglob("*")), "csv_counts": counts,
            "photo_sha256": photo_checksums, "headers_and_source_rows_verified": True,
            "attached_photos_listed_in_index": True, "sample_rows_per_table": 10,
            "sample_contains_all_referenced_observations": False, "zip_contents_verified": True,
            "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("/Volumes/MonarchSSD/data_release/publication_package"))
    parser.add_argument("--output", type=Path, default=Path("/Volumes/MonarchSSD/data_release/Zach_USGS_preview_2026-09-14"))
    parser.add_argument("--replace", action="store_true", help="Update an existing preview and ZIP")
    args = parser.parse_args()
    result = build(args.source, args.output, args.replace)
    report = Path(__file__).resolve().parents[1] / "data/release_working/usgs_preview_validation.json"
    report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
