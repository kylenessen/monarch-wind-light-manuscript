#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = ["pandas>=2.3", "numpy>=2.3", "pyproj>=3.7", "shapely>=2.1"]
# ///
"""Build the observational data release and its documentation.

Use uv run analysis/prepare_data_release.py. The portable package contains only
public tables, classification JSON, documentation and the photo collections.
Manuscript analysis inputs are generated separately in data/analysis_inputs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import from_wkb

from release_schema import analysis_30_minute, analysis_next_day, has_classification

ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_ID_CORRECTIONS = json.loads(
    (ROOT / "data/release_working/deployment_id_corrections.json").read_text()
)
DEPLOYMENT_ID_NOTE = (
    "Deployment identifiers are unique across both seasons and link all observation tables. "
    "Use deployment_id and image_filename together to link image records."
)
CLOCK_NOTE = (
    "Timestamps use device clock times without a UTC offset. "
    "The cameras and wind meters do not automatically adjust for daylight saving time. "
    "TGR1 photo times were reconstructed as described below. Other timestamps are preserved as recorded."
)
TGR1_NOTE = (
    "TGR1 photo metadata and filenames use reconstructed capture times, aligned to the "
    "deployment start and end using elapsed time in the numbered image sequence. "
    "The camera calendar jump was removed and recording gaps were retained. "
    "The visible timestamp overlay still shows the incorrect camera date and time."
)
FILENAME_NOTE = (
    "Photographs are stored in photos/deployment_id/ and named "
    "deployment_id_YYYYMMDDHHMMSS.JPG using a 24-hour clock. "
    "Deployment identifiers may contain underscores. photo_index.csv lists every image path."
)
WIND_NOTE = (
    "Wind speed is the average and gust is the maximum speed over each one-minute "
    "recording interval, in meters per second. Wind direction is the recorded average in degrees clockwise from north."
)
LOCATION_NOTE = (
    "Coordinates are approximate camera locations in WGS84, EPSG 4326, expressed in decimal degrees. "
    "Locations were recorded with a cellphone under canopy. Some points were adjusted "
    "against satellite imagery."
)
CLASSIFICATION_NOTE = (
    "classifications/ contains one JSON file per classified deployment in the native "
    "format of the Monarch Trailcam Classifier. These files retain cell positions, "
    "categories, sunlight labels and saved annotation fields. classifications.csv "
    "summarizes saved daytime classifications for use without the software. "
    "See classifications/README.md for the JSON structure and software links."
)

PUBLIC_COLUMN_NAMES = {
    "timestamp_recorded": "timestamp",
    "camera_name": "camera_id",
    "wind_sensor_name": "wind_sensor_id",
    "camera_height_m": "camera_height",
    "horizontal_distance_to_cluster_m": "horizontal_distance_to_cluster",
    "view_direction_degrees": "view_direction",
    "temperature_c": "temperature",
    "wind_speed_m_s": "wind_speed",
    "wind_gust_m_s": "wind_gust",
    "wind_direction_degrees": "wind_direction",
}

DESCRIPTIONS = {
    "deployment_id": ("Unique identifier for an uninterrupted monitoring period with a fixed camera location and view, linking photographs and associated sensor observations.", "identifier"),
    "camera_id": ("Unique identifier for an individual camera.", "identifier"),
    "wind_sensor_id": ("Unique identifier for an individual wind sensor.", "identifier"),
    "start_time": ("Deployment start in local device time, formatted as YYYY-MM-DD HH:MM:SS.", "recorded clock"),
    "end_time": ("Deployment end in local device time, formatted as YYYY-MM-DD HH:MM:SS.", "recorded clock"),
    "latitude": ("Approximate camera latitude in WGS84, EPSG 4326. Locations were recorded with a cellphone under canopy, with some points adjusted against satellite imagery.", "decimal degrees"),
    "longitude": ("Approximate camera longitude in WGS84, EPSG 4326. Locations were recorded with a cellphone under canopy, with some points adjusted against satellite imagery.", "decimal degrees"),
    "camera_height": ("Recorded camera height above ground.", "meters"),
    "horizontal_distance_to_cluster": ("Recorded horizontal viewing distance from camera to observed or expected butterfly clusters.", "meters"),
    "view_direction": ("Recorded camera viewing direction clockwise from north.", "degrees"),
    "data_quality_note": ("Deployment-specific recording, coverage or timing information.", "text"),
    "image_filename": ("Photograph filename in the form deployment_id_YYYYMMDDHHMMSS.JPG.", "identifier"),
    "timestamp": ("Observation date and time in ISO 8601 format without a UTC offset.", "recorded clock"),
    "relative_path": ("Photo path relative to the package root, grouped by deployment_id.", "path"),
    "record_user_id": ("User identifier saved in the classification JSON.", "identifier"),
    "butterfly_index": ("Butterfly Index, BI, of visible cluster size. Sum of grid-cell category lower bounds, using 0, 1, 10 and 100 for categories 0, 1-9, 10-99 and 100-999.", "BI units"),
    "sun_exposed_butterfly_index": ("BI subtotal for occupied grid cells where monarchs were observed in direct sun.", "BI units"),
    "temperature": ("Camera-overlay temperature extracted using OCR and manually reviewed.", "degrees Celsius"),
    "wind_speed": ("Average wind speed over the one-minute recording interval.", "meters per second"),
    "wind_gust": ("Maximum wind speed during the one-minute recording interval.", "meters per second"),
    "wind_direction": ("Average wind direction over the one-minute recording interval, in degrees clockwise from north, as recorded by the logger.", "degrees"),

}
for category in ("0", "1_9", "10_99", "100_999"):
    DESCRIPTIONS[f"cells_{category}"] = (f"Number of image grid cells assigned to butterfly category {category.replace('_', '-')}. Retained primitives support alternative category mappings.", "grid cells")
    if category != "0":
        DESCRIPTIONS[f"sun_exposed_cells_{category}"] = (f"Number of occupied grid cells in category {category.replace('_', '-')} marked as receiving direct sunlight.", "grid cells")

TABLES = {
    "deployments": "One row per camera deployment, including identifiers, WGS84 location, boundaries and known limitations.",
    "photo_index": "One row per retained JPEG photograph. Links images to the deployment table and collection folders.",
    "classifications": "One row per saved image classification, with counts of grid-cell categories and Butterfly Index totals. Unclassified placeholders are omitted from this summary.",
    "temperature_measurements": "One row per reviewed camera-overlay temperature measurement.",
    "wind_measurements": "One row per wind observation associated with a deployment.",
}


def manuscript_authors_and_contact():
    manuscript = (ROOT / "manuscript.tex").read_text()
    names = re.search(r"\\AuthorNames\{([^}]+)\}", manuscript)[1]
    authors = names.replace(" and ", ", ").split(", ")
    email = re.search(r"\\corres\{Correspondence: ([^\s}]+)", manuscript)[1]
    return authors, email


def read_gpkg(path, table, geometry):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        frame = pd.read_sql_query(f'SELECT * FROM "{table}"', connection)
        epsg = connection.execute("SELECT srs_id FROM gpkg_contents WHERE table_name=?", (table,)).fetchone()[0]
    transformer = Transformer.from_crs(epsg, 4326, always_xy=True)
    def coordinates(blob):
        envelope = (blob[3] >> 1) & 7
        offset = 8 + {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[envelope]
        point = from_wkb(blob[offset:])
        return transformer.transform(point.x, point.y)
    xy = frame[geometry].map(coordinates)
    frame["wgs84_longitude"] = xy.map(lambda pair: pair[0])
    frame["wgs84_latitude"] = xy.map(lambda pair: pair[1])
    return frame


def release_deployment_id(season, source_id):
    return DEPLOYMENT_ID_CORRECTIONS.get(f"{season}/{source_id}", source_id)


def release_photo_path(season, relative_path):
    path = Path(relative_path)
    source_id = path.parts[0]
    release_id = release_deployment_id(season, source_id)
    if release_id == source_id:
        return path
    if len(path.parts) != 2 or not path.name.startswith(source_id + "_"):
        raise ValueError(f"Unexpected reviewed photo path {path}")
    return Path(release_id) / (release_id + path.name[len(source_id):])


def stage_photos(archive, package, deployment, photos):
    """Expose release names without rewriting source images or duplicating their bytes."""
    source_ids = {(key.split("/", 1)[0], value): key.split("/", 1)[1]
                  for key, value in DEPLOYMENT_ID_CORRECTIONS.items()}
    for row in deployment.itertuples(index=False):
        source_id = source_ids.get((row.season, row.deployment_id), row.deployment_id)
        source = archive / ("raw/Camelot_Photos" if row.season == "2023-2024"
                            else "VSFB_2025_Deployment_Review") / source_id
        if row.deployment_id == "TGR1":
            source = archive / "corrected_photos/TGR1"
        selected = photos.loc[photos.deployment_id.eq(row.deployment_id)]
        expected = set(selected.image_filename)
        omitted = {row.deployment_id + path.name[len(source_id):]
                   for path in source.glob("*.JPG")
                   if re.fullmatch(re.escape(source_id) + r"_\d{14}_\d+\.JPG", path.name)} - expected
        target = package / "photos" / row.deployment_id
        legacy = package / "photos" / row.season / row.deployment_id
        if legacy.exists() or legacy.is_symlink():
            if target.exists() or target.is_symlink():
                raise ValueError(f"Both old and new photo directories exist {target}")
            legacy.rename(target)
        if source_id == row.deployment_id and not omitted:
            if not source.is_dir():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.symlink_to(source, target_is_directory=True)
            elif target.resolve() != source.resolve():
                raise ValueError(f"Existing photo link points to a different source {target}")
            continue
        if target.is_symlink():
            if target.resolve() != source.resolve():
                raise ValueError(f"Existing photo link points to a different source {target}")
            target.unlink()
        target.mkdir(parents=True, exist_ok=True)
        for name in omitted:
            extra = target / name
            original = source / (source_id + name[len(row.deployment_id):])
            if extra.exists():
                if not extra.samefile(original):
                    raise ValueError(f"Excluded photo differs from its source {extra}")
                extra.unlink()
        for photo in selected.itertuples(index=False):
            original = source / (source_id + photo.image_filename[len(row.deployment_id):])
            renamed = target / photo.image_filename
            if not renamed.exists():
                os.link(original, renamed)
            if not os.path.samefile(original, renamed):
                raise ValueError(f"Renamed photo differs from original {renamed}")
        if {p.name for p in target.iterdir() if p.name != ".DS_Store"} != expected:
            raise ValueError(f"Unexpected files in renamed photo directory {target}")
        previous = package / "photos" / row.season / source_id
        if previous.is_symlink() and previous.resolve() == source.resolve():
            previous.unlink()
        elif previous.exists() or previous.is_symlink():
            raise ValueError(f"Unexpected obsolete release path {previous}")
    for relative_path in photos.relative_path:
        if not (package / relative_path).is_file():
            raise ValueError(f"Released photo path does not resolve {relative_path}")
    for season in deployment.season.unique():
        legacy_parent = package / "photos" / season
        if legacy_parent.exists():
            legacy_parent.rmdir()  # Fails without deleting anything if unexpected entries remain.


def deployments(staging):
    intervals = pd.read_csv(staging / "deployment_intervals.csv", keep_default_na=False)
    excluded = json.loads((ROOT / "data/release_working/deployment_exclusions.json").read_text())
    intervals = intervals.loc[~intervals.deployment_key.isin(excluded)]
    first = read_gpkg(staging / "source_metadata/deployments_2024.gpkg", "deployments", "geom").set_index("deployment_id")
    second = read_gpkg(staging / "source_metadata/cameras_2025.gpkg", "cameras", "geometry").set_index("deployment_ID")
    observers = pd.read_csv(ROOT / "data/deployments.csv").set_index("deployment_id").Observer.to_dict()
    records = []
    for row in intervals.itertuples(index=False):
        earlier = row.season == "2023-2024"
        source = (first if earlier else second).loc[row.deployment_id]
        assert source["camera_name" if earlier else "ID"] == row.camera_name
        notes = []
        if earlier and row.deployment_id == "SC3":
            notes.append("Nonstandard deployment to capture opportunistic imagery during rocket launch.")
        if earlier and row.deployment_id == "TGR1":
            notes.append(TGR1_NOTE)
        records.append(dict(season=row.season, deployment_id=release_deployment_id(row.season, row.deployment_id),
            camera_name=row.camera_name, wind_sensor_name=row.wind_sensor_name,
            start_time_recorded=row.start_time_recorded, end_time_recorded=row.end_time_recorded,
            boundary_basis="first_season_deployment_geopackage" if earlier else "reviewed_photo_exif",
            latitude=round(source.wgs84_latitude, 8), longitude=round(source.wgs84_longitude, 8),
            camera_height_m=source["height_m" if earlier else "height"],
            horizontal_distance_to_cluster_m=source["horizontal_dist_to_cluster_m" if earlier else "view_distance"],
            view_direction_degrees=source.view_direction,
            primary_observer=observers.get(row.deployment_id, "") if earlier else "",
            data_quality_note=" ".join(notes)))
    return pd.DataFrame(records).sort_values(["season", "deployment_id"]).reset_index(drop=True)


def photo_index(archive, staging, deployment):
    records = []
    names = deployment.set_index(["season", "deployment_id"]).camera_name.to_dict()
    for folder in sorted((archive / "raw/Camelot_Photos").iterdir()):
        key = ("2023-2024", folder.name)
        if key not in names or not folder.is_dir():
            continue
        for path in sorted(folder.glob("*")):
            if path.suffix.lower() != ".jpg" or path.name.startswith("._"):
                continue
            match = re.fullmatch(re.escape(folder.name) + r"_(\d{14})(?:_\d+)?\.[Jj][Pp][Gg]", path.name)
            if not match:
                raise ValueError(f"Unexpected filename {path}")
            timestamp = pd.to_datetime(match[1], format="%Y%m%d%H%M%S").isoformat()
            records.append((*key, names[key], path.name, timestamp,
                            f"photos/{folder.name}/{path.name}"))
    manifest = pd.read_csv(staging / "reviewed_image_manifest.csv", keep_default_na=False)
    for row in manifest.itertuples(index=False):
        key = (row.season, release_deployment_id(row.season, row.deployment_id))
        if key not in names:
            continue
        relative = release_photo_path(row.season, row.relative_path)
        records.append((*key, names[key], relative.name,
                        row.capture_time_recorded, f"photos/{relative}"))
    tgr1 = pd.read_csv(ROOT / "data/release_working/tgr1_photo_times.csv")
    for row in tgr1.itertuples(index=False):
        records.append(("2023-2024", "TGR1", names[("2023-2024", "TGR1")],
                        row.image_filename, row.timestamp_recorded,
                        f"photos/TGR1/{row.image_filename}"))
    frame = pd.DataFrame(records, columns=["season", "deployment_id", "camera_name", "image_filename", "timestamp_recorded", "relative_path"])
    # Canonical unsuffixed filenames sort before collision-suffixed alternatives.
    return frame.sort_values("image_filename").drop_duplicates(
        ["deployment_id", "timestamp_recorded"], keep="first").sort_index().reset_index(drop=True)


def classifications(deployment):
    cameras = deployment.query("season == '2023-2024'").set_index("deployment_id").camera_name.to_dict()
    legacy = {"SC1": [("20231117174001", "20231118062001"), ("20231118172501", "20231119061501"), ("20231119171001", "20231120062001"), ("20231120172001", "20231121063001")],
              "SC2": [("20231117172501", "20231118062001"), ("20231118171501", "20231119061501")]}
    weights = {"0": 0, "1-9": 1, "10-99": 10, "100-999": 100}
    rows = []
    for path in sorted((ROOT / "data/deployments").glob("*.json")):
        data = json.loads(path.read_text())
        for filename, record in data.get("classifications", data).items():
            if not has_classification(record):
                continue
            compact = re.search(r"_(\d{14})", filename)[1]
            night = record.get("isNight", any(a <= compact <= b for a, b in legacy.get(path.stem, [])))
            if night:
                continue
            row = dict(season="2023-2024", deployment_id=path.stem, camera_name=cameras[path.stem],
                image_filename=filename, timestamp_recorded=pd.to_datetime(compact, format="%Y%m%d%H%M%S").isoformat(),
                record_user_id=record.get("user", ""))
            counts = dict.fromkeys(weights, 0)
            sun = dict.fromkeys(weights, 0)
            for cell in record.get("cells", {}).values():
                category = str(cell.get("count", "0")).strip()
                counts[category] += 1
                sun[category] += int(bool(cell.get("directSun", cell.get("sunlight", False))))
            row.update({"cells_" + c.replace("-", "_"): n for c, n in counts.items()})
            row.update({"sun_exposed_cells_" + c.replace("-", "_"): n for c, n in sun.items() if c != "0"})
            row["butterfly_index"] = sum(counts[c] * v for c, v in weights.items())
            row["sun_exposed_butterfly_index"] = sum(sun[c] * v for c, v in weights.items())
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["deployment_id", "timestamp_recorded"])


def dictionary(tables):
    rows = []
    for table_name, frame in tables.items():
        for column in frame:
            description, units = DESCRIPTIONS[column]
            values = frame[column].dropna()
            has_range = pd.api.types.is_numeric_dtype(values) or pd.api.types.is_bool_dtype(values) or units == "recorded clock"
            rows.append(dict(table=table_name + ".csv", column=column, description=description,
                units=units, missing_value="empty field", observed_minimum=values.min() if has_range and len(values) else "",
                observed_maximum=values.max() if has_range and len(values) else ""))
    return pd.DataFrame(rows)


def metadata_xml(tables, field_dictionary):
    root = ET.Element("metadata")
    def add(parent, path, text):
        for component in path.split("/"):
            child = parent.find(component)
            parent = child if child is not None else ET.SubElement(parent, component)
        parent.text = str(text)
    authors, email = manuscript_authors_and_contact()
    citation = ET.SubElement(ET.SubElement(root, "idinfo"), "citation")
    citeinfo = ET.SubElement(citation, "citeinfo")
    for author in authors:
        ET.SubElement(citeinfo, "origin").text = author
    add(root, "idinfo/citation/citeinfo/pubdate", "Unpublished material")
    add(root, "idinfo/citation/citeinfo/title", "Photographs, image classifications, wind measurements, and image-derived temperatures from monarch butterfly monitoring at Vandenberg Space Force Base, California, 2023 through 2025")
    add(root, "idinfo/citation/citeinfo/geoform", "tabular digital data, JSON image annotations and digital photographs")
    add(root, "idinfo/descript/abstract", "Observations from monarch monitoring at Vandenberg Space Force Base during the 2023-2024 and 2024-2025 overwintering seasons. Includes deployment information, photographs, wind measurements, native classification JSON and a tabular summary, and reviewed camera-overlay temperatures. The archive includes monitoring beyond the subset analyzed in the associated manuscript.")
    add(root, "idinfo/descript/purpose", "Preserve monitoring observations for future research. Manuscript analysis inputs, scripts and results are maintained at https://github.com/kylenessen/monarch-wind-light-manuscript.")
    add(root, "idinfo/descript/supplinf", CLOCK_NOTE + " " + TGR1_NOTE + " " + FILENAME_NOTE + " " + DEPLOYMENT_ID_NOTE + " " + CLASSIFICATION_NOTE)
    dep = tables["deployments"]
    add(root, "idinfo/timeperd/timeinfo/rngdates/begdate", dep.start_time.min()[:10].replace("-", ""))
    add(root, "idinfo/timeperd/timeinfo/rngdates/enddate", dep.end_time.max()[:10].replace("-", ""))
    add(root, "idinfo/timeperd/current", "Recorded deployment and photograph times.")
    add(root, "idinfo/status/progress", "In work")
    add(root, "idinfo/status/update", "As needed")
    for name, value in {"westbc": dep.longitude.min(), "eastbc": dep.longitude.max(), "northbc": dep.latitude.max(), "southbc": dep.latitude.min()}.items():
        add(root, "idinfo/spdom/bounding/" + name, value)
    add(root, "idinfo/keywords/theme/themekt", "None")
    add(root, "idinfo/keywords/theme/themekey", "monarch butterfly, overwintering, wind, image classification, Butterfly Index")
    add(root, "idinfo/keywords/place/placekt", "None")
    add(root, "idinfo/keywords/place/placekey", "Vandenberg Space Force Base, Santa Barbara County, California")
    add(root, "idinfo/accconst", "REVIEW_REQUIRED release access terms")
    add(root, "idinfo/useconst", "REVIEW_REQUIRED release use terms")
    add(root, "idinfo/ptcontac/cntinfo/cntperp/cntper", authors[0])
    add(root, "idinfo/ptcontac/cntinfo/cntperp/cntorg", "Biological Sciences Department, California Polytechnic State University")
    add(root, "idinfo/ptcontac/cntinfo/cntemail", email)
    add(root, "dataqual/attracc/attraccr", WIND_NOTE + " Camera-overlay temperatures were extracted with OCR and manually reviewed. Camera readings were not calibrated against a reference thermometer. BI is an index of visible cluster size calculated from ordinal grid-cell classifications.")
    add(root, "dataqual/logic", "deployment_id uniquely identifies each deployment. Photos link by deployment_id and image_filename. Exact wind tuples are deduplicated within sensors before assigning deployment intervals.")
    add(root, "dataqual/complete", "Classifications and reviewed temperatures cover the first season. Photographs and available wind measurements cover both seasons. Deployment-specific recording information is in deployments.csv. The classification summary excludes night records and unclassified placeholders. Native JSON files retain the full annotations. Unclassified photographs do not establish butterfly absence. Missing CSV values are empty fields.")
    add(root, "dataqual/posacc/horizpa/horizpar", LOCATION_NOTE + " First-season coordinates were already in WGS84. Second-season points were transformed from EPSG 3498 to EPSG 4326.")
    lineage = ET.SubElement(root.find("dataqual"), "lineage")
    for text in (
        "First-season deployment intervals and positions were read from the original deployment GeoPackage. Second-season retained photograph EXIF extrema set the release boundaries. Coordinates were transformed to WGS84 where needed. Deployment and wind timestamps were preserved.",
        TGR1_NOTE + " The first and last image times were anchored to the field deployment start and end. Intermediate times were linearly scaled by elapsed camera time after removing the 31-day calendar jump. EXIF capture, creation and modification times were updated in release copies. Image pixels and original source photographs were unchanged.",
        FILENAME_NOTE,
        "One photograph per deployment and capture timestamp was retained. Where multiple images shared a timestamp, the unsuffixed photograph was retained.",
        DEPLOYMENT_ID_NOTE,
        "Wind records from 92 SQLite databases were matched to the assigned wind meter and inclusive deployment interval. Whitespace and numeric representations were normalized. Identical sensor, time, speed, gust and direction tuples were deduplicated. Source IDs were not treated as globally unique. Off-interval and unrelated observations were omitted. Conflicting measurement tuples would be retained for review. Raw source databases remain unchanged.",
        "Native classification JSON files were included with their cell positions and annotation fields. Saved daytime annotations were summarized as category counts and BI in classifications.csv. BI uses category lower bounds of 0, 1, 10 and 100. Night records were excluded using saved night flags and recorded SC1 and SC2 night intervals when flags were absent.",
        "Camera-overlay temperatures were extracted using OCR, reviewed as deployment time series and manually corrected for extraction errors. The reviewed values are included in temperature_measurements.csv.",
    ):
        step = ET.SubElement(lineage, "procstep")
        add(step, "procdesc", text)
        add(step, "procdate", "20260914" if text.startswith(TGR1_NOTE) else "20260913")
    add(root, "spdoinfo/indspref", "Photographs and tabular observations relate to camera deployment points through deployment_id.")
    add(root, "spdoinfo/direct", "Point")
    add(root, "spdoinfo/ptvctinf/sdtsterm/sdtstype", "Entity point")
    add(root, "spdoinfo/ptvctinf/sdtsterm/ptvctcnt", len(dep))
    add(root, "spref/horizsys/geograph/latres", "0.00000001")
    add(root, "spref/horizsys/geograph/longres", "0.00000001")
    add(root, "spref/horizsys/geograph/geogunit", "Decimal degrees")
    add(root, "spref/horizsys/geodetic/horizdn", "D_WGS_1984")
    add(root, "spref/horizsys/geodetic/ellips", "WGS_1984")
    add(root, "spref/horizsys/geodetic/semiaxis", "6378137.0")
    add(root, "spref/horizsys/geodetic/denflat", "298.257223563")
    ea = ET.SubElement(root, "eainfo")
    for table_name in tables:
        detailed = ET.SubElement(ea, "detailed")
        add(detailed, "enttyp/enttypl", table_name + ".csv")
        add(detailed, "enttyp/enttypd", TABLES[table_name])
        add(detailed, "enttyp/enttypds", "Study investigators and analysis preparation code")
        for row in field_dictionary.loc[field_dictionary.table.eq(table_name + ".csv")].itertuples(index=False):
            attr = ET.SubElement(detailed, "attr")
            add(attr, "attrlabl", row.column)
            add(attr, "attrdef", row.description + f" Units {row.units}. Missing values are empty fields.")
            add(attr, "attrdefs", "Study source data and processing code")
            add(attr, "attrdomv/udom", "Observed values. Observed minimum and maximum in data_dictionary.csv are descriptive, not validation limits.")
    add(ea, "overview/eaover", FILENAME_NOTE + " " + CLASSIFICATION_NOTE + " " + " ".join(f"{name}.csv contains {len(frame):,} rows." for name, frame in tables.items()))
    add(ea, "overview/eadetcit", "data_dictionary.csv, README.md and classifications/README.md in this package. Classifier source code https://github.com/kylenessen/monarch_trailcam_classifier.")
    add(root, "distinfo/resdesc", "CSV observation tables, native classification JSON files, JPEG photograph collections, metadata XML and documentation.")
    add(root, "distinfo/distliab", "REVIEW_REQUIRED applicable USGS distribution statement after review. No release approval is claimed by this draft.")
    add(root, "metainfo/metd", "20260914")
    add(root, "metainfo/metc/cntinfo/cntorgp/cntorg", "REVIEW_REQUIRED responsible metadata organization")
    add(root, "metainfo/metc/cntinfo/cntemail", "REVIEW_REQUIRED shared group email")
    add(root, "metainfo/metstdn", "FGDC Content Standard for Digital Geospatial Metadata")
    add(root, "metainfo/metstdv", "FGDC-STD-001-1998")
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def validate(tables):
    dep = tables["deployments"]
    assert all("season" not in frame.columns for frame in tables.values())
    assert dep.deployment_id.is_unique, "Deployment identifiers must be unique across seasons"
    assert dep.latitude.between(34, 35).all() and dep.longitude.between(-121, -120).all()
    keys = set(dep.deployment_id)
    photos = tables["photo_index"]
    assert not photos.duplicated(["deployment_id", "image_filename"]).any()
    assert photos.image_filename.is_unique, "Released photo filenames must be globally unique"
    assert photos.relative_path.is_unique
    assert not photos.duplicated(["deployment_id", "timestamp_recorded"]).any()
    for name in ("photo_index", "classifications", "temperature_measurements", "wind_measurements"):
        frame = tables[name]
        assert set(frame.deployment_id) <= keys, name
    photo_keys = set(zip(photos.deployment_id, photos.image_filename))
    for name in ("classifications", "temperature_measurements"):
        frame = tables[name]
        assert set(zip(frame.deployment_id, frame.image_filename)) <= photo_keys, name
    wind = tables["wind_measurements"]
    assert not wind.duplicated().any()
    linked = wind.merge(dep[["deployment_id", "start_time_recorded", "end_time_recorded"]], on="deployment_id", validate="many_to_one")
    time = pd.to_datetime(linked.timestamp_recorded, format="mixed")
    assert time.ge(pd.to_datetime(linked.start_time_recorded, format="mixed")).all()
    assert time.le(pd.to_datetime(linked.end_time_recorded, format="mixed")).all()
    classification = tables["classifications"]
    assert classification.sun_exposed_butterfly_index.le(classification.butterfly_index).all()
    return dict(table_rows={name: len(frame) for name, frame in tables.items()},
                schema_and_join_checks="passed", photo_time_reconstruction="TGR1 deployment endpoints")


def stage_classifications(destination):
    target = destination / "classifications"
    target.mkdir(parents=True, exist_ok=True)
    files = sorted((ROOT / "data/deployments").glob("*.json"))
    for path in files:
        shutil.copyfile(path, target / path.name)
    (target / "README.md").write_text("""# Image classifications

Each deployment JSON contains the native annotations for its photographs. The
deployment identifier in the JSON filename matches deployments.csv. Image keys
match image_filename in photo_index.csv.

The source code and illustrated protocol are available from the
[Monarch Trailcam Classifier](https://github.com/kylenessen/monarch_trailcam_classifier)
and its [classification guide](https://kylenessen.github.io/monarch_trailcam_classifier/).

Files contain an object keyed by image filename, either at the top level or within
a classifications object. Each image record contains cells keyed by cell_row_column.
Each cell stores count, an ordinal category, and directSun, a sunlight flag. Some
older records use sunlight for the same flag. Categories are 0, 1-9, 10-99 and
100-999. Image records also contain confirmed and index, and may contain user,
isNight and notes. These retain confirmation state, image sequence, saved user,
night flag and annotation notes.

The JSON includes unclassified placeholders. classifications.csv summarizes
saved daytime classifications, including unconfirmed annotations and excluding
untouched placeholders. Night records are identified using saved night flags and
recorded SC1 and SC2 night intervals when a JSON flag is absent. Butterfly Index sums category lower bounds of 0, 1, 10 and 100.
Sun-exposed Butterfly Index sums those values for occupied cells marked in sunlight.
""")
    return len(files)


def release_readme(tables):
    authors, email = manuscript_authors_and_contact()
    contents = "\n\n".join(
        f"[{name}.csv]({name}.csv) contains {len(frame):,} rows. {TABLES[name]}"
        for name, frame in tables.items()
    )
    return (
        "# Monarch monitoring observations, 2023-2025\n\n"
        + ", ".join(authors) + ".\n\nContact " + authors[0] + ", " + email + ".\n\n"
        "This release preserves observations from both monitoring seasons at Vandenberg "
        "Space Force Base, including deployments outside the manuscript analysis subset. "
        "Photographs and available wind measurements cover both seasons. Image classifications "
        "and reviewed camera-overlay temperatures cover the first season.\n\n"
        + contents + "\n\n" + CLASSIFICATION_NOTE + "\n\n" + FILENAME_NOTE + "\n\n"
        + DEPLOYMENT_ID_NOTE + " Missing CSV values are empty fields. "
        "[data_dictionary.csv](data_dictionary.csv) defines the table fields.\n\n"
        + CLOCK_NOTE + "\n\n" + TGR1_NOTE + "\n\n"
        + LOCATION_NOTE + " "
        "Deployment-specific recording information is in deployments.csv.\n\n"
        + WIND_NOTE + " Wind measurements are provided as recorded within deployment intervals.\n\n"
        "Temperature values were extracted from camera overlays using OCR and manually reviewed. "
        "The camera readings were not calibrated against a reference thermometer. "
        "BI is an index of visible cluster size based on ordinal image-cell categories. "
        "Unclassified photographs do not establish butterfly absence.\n\n"
        "The [manuscript repository](https://github.com/kylenessen/monarch-wind-light-manuscript) "
        "contains the analysis inputs, scripts and results for reproducing the paper. "
        "[metadata.xml](metadata.xml) describes this observational release.\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("/Volumes/MonarchSSD/data_release"))
    parser.add_argument("--reconciliation", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/release")
    parser.add_argument("--package-dir", type=Path)
    parser.add_argument("--analysis-output-dir", type=Path, default=ROOT / "data/analysis_inputs")
    parser.add_argument("--analysis-only", action="store_true", help="Rebuild the two analysis CSVs without the portable drive")
    args = parser.parse_args()
    if args.analysis_only:
        tables = {
            "analysis_30_minute": analysis_30_minute(pd.read_csv(ROOT / "data/monarch_analysis_lag30min.csv")),
            "analysis_next_day": analysis_next_day(pd.read_csv(ROOT / "data/monarch_daily_lag_analysis_nextday_window.csv")),
        }
        args.analysis_output_dir.mkdir(parents=True, exist_ok=True)
        for name, frame in tables.items():
            frame.to_csv(args.analysis_output_dir / f"{name}.csv", index=False)
        return
    staging = args.reconciliation or args.archive / "reconciled_2026-09-13"
    dep = deployments(staging)
    photos = photo_index(args.archive, staging, dep)
    temp = pd.read_csv(ROOT / "data/temperature_data_2023.csv").rename(columns={"filename": "image_filename", "temperature": "temperature_c"})
    temp["season"] = "2023-2024"
    temp["timestamp_recorded"] = pd.to_datetime(temp.timestamp.astype(str), format="%Y%m%d%H%M%S").dt.strftime("%Y-%m-%dT%H:%M:%S")
    temp = temp.merge(dep[["season", "deployment_id", "camera_name"]], on=["season", "deployment_id"], validate="many_to_one")
    temp = temp[["season", "deployment_id", "camera_name", "image_filename", "timestamp_recorded", "temperature_c"]]
    wind = pd.read_csv(staging / "wind_measurements.csv", low_memory=False)
    wind["deployment_id"] = [release_deployment_id(season, identifier)
                             for season, identifier in zip(wind.season, wind.deployment_id)]
    wind = wind.merge(dep[["season", "deployment_id"]], on=["season", "deployment_id"], validate="many_to_one")
    wind = wind[["season", "deployment_id", "wind_sensor_name", "timestamp_recorded", "wind_speed_m_s", "wind_gust_m_s", "wind_direction_degrees"]]
    tables = dict(deployments=dep, photo_index=photos, classifications=classifications(dep), temperature_measurements=temp, wind_measurements=wind)
    # Season remains internal source provenance only. Public joins use deployment_id.
    tables = {name: frame.drop(columns="season", errors="ignore") for name, frame in tables.items()}
    validation = validate(tables)
    # Validate against the source boundaries before simplifying their public display.
    public_deployments = tables["deployments"].drop(columns=["boundary_basis", "primary_observer"]).rename(
        columns={"start_time_recorded": "start_time", "end_time_recorded": "end_time"})
    for column in ("start_time", "end_time"):
        public_deployments[column] = pd.to_datetime(
            public_deployments[column], format="mixed").dt.strftime("%Y-%m-%d %H:%M:%S")
    tables["deployments"] = public_deployments
    tables = {name: frame.rename(columns=PUBLIC_COLUMN_NAMES) for name, frame in tables.items()}
    fields = dictionary(tables)
    xml = metadata_xml(tables, fields)
    readme = release_readme(tables)
    package = args.package_dir or args.archive / "publication_package"
    for destination in (args.output_dir, package):
        destination.mkdir(parents=True, exist_ok=True)
        for name, frame in tables.items():
            frame.to_csv(destination / f"{name}.csv", index=False, na_rep="", lineterminator="\n")
        fields.to_csv(destination / "data_dictionary.csv", index=False, na_rep="")
        (destination / "metadata.xml").write_bytes(xml)
        (destination / "README.md").write_text(readme)
        stage_classifications(destination)
        for name in ("analysis_30_minute.csv", "analysis_next_day.csv"):
            (destination / name).unlink(missing_ok=True)
    stage_photos(args.archive, package, dep, photos)
    validation["photo_paths_resolve"] = len(photos)
    validation["deployment_ids_globally_unique"] = True
    validation["photo_filenames_globally_unique"] = True
    validation["deployment_id_corrections"] = DEPLOYMENT_ID_CORRECTIONS
    (ROOT / "data/release_working/validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    print(json.dumps(validation, indent=2))
    print(f"Public staging package {package}")


if __name__ == "__main__":
    main()
