#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = ["pandas>=2.3", "numpy>=2.3", "pyproj>=3.7", "shapely>=2.1"]
# ///
"""Build the public tables from frozen sources without editing observations.

Use uv run analysis/prepare_data_release.py. The portable package contains only
public tables, README, metadata XML and links to the existing photo collections.
Reconciliation provenance and review decisions stay outside that package.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import from_wkb

from release_schema import analysis_30_minute, analysis_next_day, has_classification

ROOT = Path(__file__).resolve().parents[1]
CLOCK_NOTE = (
    "Camera and wind-meter clocks do not automatically apply daylight saving time. "
    "For the 2024-2025 season, timestamps remain on the recorded device clocks. "
    "No daylight saving or UTC conversion was applied to either series during release preparation. "
    "Apparent image lighting and civil clock time may therefore differ by one hour. "
    "Repeated clock times identify distinct photos and are retained. "
    "The investigator reports accounting for seasonal clock changes during first-season processing, "
    "but the exact historical procedure has not been recovered. Existing first-season timestamps "
    "are preserved. No UTC offset or independently verified camera-to-logger synchronization is asserted."
)
FILENAME_NOTE = (
    "Photographs are grouped in photos/season/deployment_id/. Image filenames use "
    "deployment_id_YYYYMMDDHHMMSS.JPG, corresponding to the format code %Y%m%d%H%M%S. "
    "The deployment identifier may itself contain an underscore. The timestamp has a four-digit "
    "year followed by two-digit month, day, 24-hour hour, minute and second. It carries no timezone. "
    "For the reviewed second season it comes from the photo EXIF capture time. Existing first-season "
    "canonical filenames are preserved. Distinct second-season photos sharing a timestamp use "
    "the unsuffixed name and an _02 suffix before .JPG. This suffix is a collision counter, "
    "not a fractional second, ordering guarantee, or clock correction. The photo index links every "
    "released filename to its deployment folder. One collection-level description applies to all "
    "images in each deployment folder. Individual photo metadata records are not required."
)
WIND_NOTE = (
    "Wind speed and gust are in meters per second. Direction is reported in degrees clockwise "
    "from north, with 360 representing north. The instrument manual specifies a 16-point sensor "
    "with 22.5-degree resolution and averaged logging. The database contains integer directions "
    "throughout 0 to 360, so exported observations are not restricted to 45-degree increments. "
    "The investigator considers direction 0 invalid or suspect. That interpretation has not been "
    "confirmed in the manufacturer manual, so original zeros are retained and should not be treated "
    "as confirmed north. Blank is missing. Zero speed or gust is not automatically invalid. "
    "Manual https://rainwise.com/downloads/windsoft/WindLog140805%20.pdf, section 7.2. "
    "Matching source databases use Units code 2, consistent with the manuscript m/s convention."
)

DESCRIPTIONS = {
    "season": ("Field season. Use season together with deployment_id as the deployment key, because SC12 recurs across seasons.", "identifier"),
    "deployment_id": ("Field deployment identifier. Unique within a season. Both analysis tables and all classifications and temperatures are from 2023-2024.", "identifier"),
    "camera_name": ("Field name assigned to the camera. Join deployments using season and deployment_id.", "identifier"),
    "wind_sensor_name": ("Field name assigned to the wind meter. A meter may serve multiple camera views or deployments.", "identifier"),
    "start_time_recorded": ("Deployment start from the original first-season deployment layer, or earliest retained EXIF capture time in the reviewed second-season photos. Source fractional seconds are preserved.", "recorded clock"),
    "end_time_recorded": ("Deployment end from the original first-season deployment layer, or latest retained EXIF capture time in the reviewed second-season photos. This is not necessarily the last wind observation.", "recorded clock"),
    "boundary_basis": ("first_season_deployment_geopackage means source deployment-layer boundaries. reviewed_photo_exif means minimum and maximum retained photo EXIF times.", "text"),
    "latitude": ("Latitude of the camera deployment in WGS84, EPSG 4326. Coordinate precision does not establish positional accuracy.", "decimal degrees"),
    "longitude": ("Longitude of the camera deployment in WGS84, EPSG 4326. Western longitudes are negative.", "decimal degrees"),
    "camera_height_m": ("Recorded camera height above ground.", "meters"),
    "horizontal_distance_to_cluster_m": ("Recorded horizontal viewing distance from camera to butterfly cluster.", "meters"),
    "view_direction_degrees": ("Recorded camera viewing direction clockwise from north.", "degrees"),
    "primary_observer": ("Primary classifier assigned to the deployment in the manuscript metadata. This does not identify an independent replicate observer for every image.", "text"),
    "data_quality_note": ("Known recording, coverage or timing limitations. Empty means no additional deployment-specific note here, not certification of error-free observations.", "text"),
    "image_filename": ("Canonical photo filename. Join with season and deployment_id to photo_index. See filename convention in README and metadata XML.", "identifier"),
    "timestamp_recorded": ("Recorded date and time in ISO 8601 extended form without UTC offset. No new clock correction was applied. Image times are EXIF-derived for second-season photos and filename-derived for first-season products.", "recorded clock"),
    "relative_path": ("Photo path relative to the package root, grouped by season and deployment_id.", "path"),
    "record_user_id": ("User identifier saved in the annotation record, possibly a later editor. Blank means absent from the source. The assigned primary observer is reported separately.", "identifier"),
    "classification_confirmed": ("True if the annotation software marked the record confirmed. Unconfirmed records are included only when a user or a nondefault annotation provides evidence of classification.", "boolean"),
    "is_night": ("Night flag from the annotation record, or historical SC1/SC2 night intervals when the flag was absent. This is an existing classification convention, not a newly inferred timezone.", "boolean"),
    "butterfly_index": ("Butterfly Index, BI, of visible cluster size. Sum of grid-cell category lower bounds, using 0, 1, 10 and 100 for categories 0, 1-9, 10-99 and 100-999. This is not an individual butterfly count.", "BI units"),
    "sun_exposed_butterfly_index": ("BI subtotal for occupied grid cells marked directSun, or legacy sunlight. Cannot exceed total BI. No change or delta is included in this observation table.", "BI units"),
    "temperature_c": ("Approximate local camera temperature extracted from the image overlay, with prior manual review of OCR. Existing reviewed values are preserved. This is not a newly calibrated ambient-air measurement.", "degrees Celsius"),
    "wind_speed_m_s": ("Wind speed reported in the logger speed field for the recording interval.", "meters per second"),
    "wind_gust_m_s": ("Maximum wind gust reported in the logger gust field for the recording interval, normally one minute.", "meters per second"),
    "wind_direction_degrees": (WIND_NOTE, "degrees"),
    "deployment_day_id": ("Deployment and calendar-day grouping used for random intercepts and within-day residual correlation in the 30-minute analysis.", "identifier"),
    "observation_order": ("Original sequence index of the current observation within deployment-day for the 30-minute analysis, or current day within deployment for next-day analysis. Gaps are retained for AR(1) correlation.", "integer"),
    "previous_image_filename": ("Earlier photo in the retained 30-minute pair. First-season photo_index provides its path.", "identifier"),
    "current_image_filename": ("Later photo in the retained 30-minute pair. First-season photo_index provides its path.", "identifier"),
    "previous_timestamp_recorded": ("Recorded earlier image time in the retained pair. No new timezone conversion.", "recorded clock"),
    "current_timestamp_recorded": ("Recorded later image time in the retained pair. No new timezone conversion.", "recorded clock"),
    "previous_bi": ("BI of the earlier image. Adjustment covariate and input to descriptive statistics.", "BI units"),
    "current_bi": ("BI of the later image. Used in descriptive and occupied-cluster wind summaries.", "BI units"),
    "delta_bi": ("Change in BI. Current minus previous image BI for 30-minute pairs. Current-day maximum minus previous-day maximum BI for next-day pairs.", "BI units"),
    "delta_bi_signed_cuberoot": ("Signed cube root of delta_bi, the 30-minute model response. Stored transformation preserved from the manuscript input.", "transformed BI units"),
    "previous_sun_exposed_bi": ("Sun-exposed BI of the earlier image in the 30-minute pair.", "BI units"),
    "mean_temperature_c": ("Arithmetic mean of the earlier and later image-overlay temperatures.", "degrees Celsius"),
    "maximum_wind_gust_m_s": ("Maximum recorded gust in the analysis window. The 30-minute preparation uses a fixed 30-minute wind window ending at the later image, even if the photo pair differs by up to five minutes.", "meters per second"),
    "minutes_since_first_daily_observation": ("Minutes since the first observation in the upstream deployment-day series. Historical code called this time_within_day_t. The manuscript called it time since sunrise, but the code does not calculate astronomical sunrise.", "minutes"),
    "minutes_gust_at_or_above_2_m_s": ("Number of source one-minute records with gust >= 2 m/s in the 30-minute window. Used in descriptive summaries. This counts minute maxima, not continuous exposure above a threshold.", "one-minute records"),
    "previous_day_maximum_bi": ("Maximum BI on the earlier day. Adjustment covariate in next-day models.", "BI units"),
    "window_duration_hours": ("Duration from previous-day maximum BI time to current-day final daytime observation.", "hours"),
    "minimum_temperature_c": ("Minimum reviewed camera-overlay temperature in the next-day window.", "degrees Celsius"),
    "maximum_temperature_c": ("Maximum reviewed camera-overlay temperature in the next-day window.", "degrees Celsius"),
    "temperature_at_previous_day_maximum_c": ("Reviewed camera-overlay temperature at the earlier day's maximum BI.", "degrees Celsius"),
    "cumulative_sun_exposed_bi": ("Sum of sun-exposed BI across daytime image observations in the next-day window. Combines the indexed abundance in sunlit cells and the number of observations, not a continuous radiation dose.", "BI units"),
}
for category in ("0", "1_9", "10_99", "100_999"):
    DESCRIPTIONS[f"cells_{category}"] = (f"Number of image grid cells assigned to butterfly category {category.replace('_', '-')}. Retained primitives support alternative category mappings.", "grid cells")
    if category != "0":
        DESCRIPTIONS[f"sun_exposed_cells_{category}"] = (f"Number of occupied grid cells in category {category.replace('_', '-')} marked as receiving direct sunlight.", "grid cells")

TABLES = {
    "deployments": "One row per season and camera deployment, including identifiers, WGS84 location, boundaries and known limitations.",
    "photo_index": "One row per retained JPEG photograph. Links images to the deployment table and collection folders.",
    "classifications": "One row per image with evidence of classification, with ordinal cell primitives and BI totals. Unclassified placeholders are omitted. Covers the first season only.",
    "temperature_measurements": "One row per reviewed first-season image-overlay temperature record, including missing temperature values. No second-season temperature extraction was supplied.",
    "wind_measurements": "One row per distinct wind observation associated with an assigned deployment interval. Identical observations within an instrument are deduplicated. SC9 and SC10 share StarDust observations because both deployment records assign that sensor during overlapping intervals. These shared rows are not independent measurements.",
    "analysis_30_minute": "Retained 30-minute manuscript input, with only variables used by the primary analyses, descriptive summaries and focused observer sensitivity. Both-zero BI pairs were excluded upstream. Photo-pair tolerance is five minutes. Row order and values are preserved.",
    "analysis_next_day": "Retained next-day manuscript input after >=95 percent overall coverage and complete-case selection. Deployment-days contain 15-25 daytime observations, consecutive days are paired, and pairs with both daily maxima zero are excluded. Coverage is the geometric mean of temperature, wind and daylight-image coverage. Source observation-order gaps are preserved. Signed square-root delta BI is calculated in R.",
}


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
        if earlier and row.deployment_id == "UDMH1":
            notes.append("Source field notes describe wind data as corrupted. Recorded values are preserved and require caution.")
        if earlier and row.deployment_id == "TGR1":
            notes.append("Source notes report that the camera date was not set. No reviewed photographs are included for this deployment.")
        if not earlier and row.deployment_id == "PS01":
            notes.append("Available wind series ends January 31, 2025 at 04:04. Cause of cessation is unknown.")
        if not earlier and row.deployment_id == "SC12":
            notes.append("Regular wind sequence ends December 23, 2024 at 12:51. After a 22-day gap, 69 zero-speed and zero-gust records occur January 14, 2025. Their field or servicing context is uncertain. Values are preserved.")
        if not earlier and row.deployment_id not in ("PS01", "SC12"):
            notes.append("No located wind records match the assigned sensor and reviewed photo interval.")
        records.append(dict(season=row.season, deployment_id=row.deployment_id,
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
                            f"photos/{key[0]}/{folder.name}/{path.name}"))
    manifest = pd.read_csv(staging / "reviewed_image_manifest.csv", keep_default_na=False)
    for row in manifest.itertuples(index=False):
        key = (row.season, row.deployment_id)
        if key not in names:
            continue
        records.append((*key, names[key], Path(row.relative_path).name,
                        row.capture_time_recorded, f"photos/{row.season}/{row.relative_path}"))
    return pd.DataFrame(records, columns=["season", "deployment_id", "camera_name", "image_filename", "timestamp_recorded", "relative_path"])


def classifications(deployment):
    observers = deployment.query("season == '2023-2024'").set_index("deployment_id").primary_observer.to_dict()
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
            row = dict(season="2023-2024", deployment_id=path.stem, camera_name=cameras[path.stem],
                image_filename=filename, timestamp_recorded=pd.to_datetime(compact, format="%Y%m%d%H%M%S").isoformat(),
                primary_observer=observers[path.stem], record_user_id=record.get("user", ""),
                classification_confirmed=bool(record.get("confirmed")), is_night=bool(night))
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
    add(root, "idinfo/citation/citeinfo/origin", "REVIEW_REQUIRED release author list and order")
    add(root, "idinfo/citation/citeinfo/pubdate", "Unpublished material")
    add(root, "idinfo/citation/citeinfo/title", "Photographs, image classifications, wind measurements, and image-derived temperatures from monarch butterfly monitoring at Vandenberg Space Force Base, California, 2023 through 2025")
    add(root, "idinfo/citation/citeinfo/geoform", "tabular digital data and digital photographs")
    add(root, "idinfo/descript/abstract", "Draft release of available observations from two monarch overwintering monitoring seasons. Includes deployment locations and recorded intervals, photographs, first-season ordinal image classifications and reviewed camera-overlay temperatures, wind observations from both seasons where available, and two first-season manuscript analysis tables. Unclassified photographs do not establish butterfly absence. BI is an index of visible cluster size rather than a count of individual butterflies.")
    add(root, "idinfo/descript/purpose", "Preserve field observations for reuse and provide inputs for reproducing the associated wind and light analyses. Analysis scripts are maintained in the repository, not distributed as data-release files. Repository https://github.com/kylenessen/monarch-wind-light-manuscript. Pin the final release commit before publication.")
    add(root, "idinfo/descript/supplinf", CLOCK_NOTE + " " + FILENAME_NOTE)
    dep = tables["deployments"]
    add(root, "idinfo/timeperd/timeinfo/rngdates/begdate", dep.start_time_recorded.min()[:10].replace("-", ""))
    add(root, "idinfo/timeperd/timeinfo/rngdates/enddate", dep.end_time_recorded.max()[:10].replace("-", ""))
    add(root, "idinfo/timeperd/current", "Recorded deployment-layer and reviewed photograph times. See clock caveat.")
    add(root, "idinfo/status/progress", "In work")
    add(root, "idinfo/status/update", "As needed")
    for name, value in {"westbc": dep.longitude.min(), "eastbc": dep.longitude.max(), "northbc": dep.latitude.max(), "southbc": dep.latitude.min()}.items():
        add(root, "idinfo/spdom/bounding/" + name, value)
    add(root, "idinfo/keywords/theme/themekt", "None")
    add(root, "idinfo/keywords/theme/themekey", "monarch butterfly, overwintering, wind, image classification, Butterfly Index")
    add(root, "idinfo/keywords/place/placekt", "None")
    add(root, "idinfo/keywords/place/placekey", "Vandenberg Space Force Base, Santa Barbara County, California")
    add(root, "idinfo/accconst", "REVIEW_REQUIRED release access terms")
    add(root, "idinfo/useconst", "Draft metadata and data package for review. No institutional approval or final DOI is asserted. " + CLOCK_NOTE)
    add(root, "dataqual/attracc/attraccr", WIND_NOTE + " Camera-overlay temperatures were reviewed for OCR errors but are approximate camera measurements, not independently calibrated air temperatures. Classification primitives and source measurements are preserved.")
    add(root, "dataqual/logic", "Season and deployment_id jointly identify deployments. Photos link by season, deployment_id and image_filename. Exact wind tuples are deduplicated within sensors before assigning deployment intervals. Shared sensor observations for SC9 and SC10 remain associated with both camera deployments and are not independent measurements.")
    add(root, "dataqual/complete", "Available records are incomplete for some deployments. No second-season classification or reviewed temperature table was supplied. Deployment data_quality_note records absent wind coverage, corrupted wind records and uncertain later zero-valued records. Blank values are missing. Untouched unclassified zero placeholders are excluded from classifications. Analysis tables preserve historical manuscript inputs, including an unresolved unconfirmed zero observation identified in README. No missing observations are imputed.")
    add(root, "dataqual/posacc/horizpa/horizpar", "First-season coordinates are WGS84 source deployment points. Second-season camera points were transformed from EPSG 3498, NAD83(NSRS2007) / California zone 5 in US survey feet, to EPSG 4326 using pyproj with longitude-first output. Positional accuracy was not independently measured. Decimal precision is not an accuracy estimate.")
    lineage = ET.SubElement(root.find("dataqual"), "lineage")
    for text in (
        "First-season deployment intervals and positions were read from the original deployment GeoPackage. Second-season retained photograph EXIF extrema set the release boundaries. Only coordinate representations were transformed to WGS84. No instrument or image timestamps were changed.",
        FILENAME_NOTE,
        "Wind records from 92 SQLite databases were matched to the assigned wind meter and inclusive deployment interval. Whitespace and numeric representations were normalized. Identical sensor, time, speed, gust and direction tuples were deduplicated. Source IDs were not treated as globally unique. Off-interval and unrelated observations were omitted. Conflicting measurement tuples would be retained for review. Raw source databases remain unchanged.",
        "Saved classification categories were summarized into grid-cell counts and lower-bound BI. Confirmed records, records with a saved user, and nondefault annotations are retained. Untouched unconfirmed zero placeholders are omitted. Reviewed first-season camera-overlay temperatures were copied without recalibration. No new temperature extraction was performed.",
        "Historical analysis inputs were reduced to columns used by the retained analyses and renamed to BI, delta BI and explicit weather terms. Selection rules and input values were preserved. The next-day table applies the historical coverage threshold of 0.95 and complete-case filter. The time covariate is minutes since the first daily observation, not a calculated sunrise time.",
    ):
        step = ET.SubElement(lineage, "procstep")
        add(step, "procdesc", text)
        add(step, "procdate", "20260913")
    add(root, "spdoinfo/indspref", "Photographs and tabular observations relate to camera deployment points through season and deployment_id.")
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
    add(ea, "overview/eaover", FILENAME_NOTE + " " + " ".join(f"{name}.csv contains {len(frame):,} rows." for name, frame in tables.items()))
    add(ea, "overview/eadetcit", "data_dictionary.csv and README.md in this package")
    add(root, "distinfo/resdesc", "Draft package of CSV tables, JPEG photograph collections, metadata XML and README. Scripts are in the GitHub repository.")
    add(root, "distinfo/distliab", "REVIEW_REQUIRED applicable USGS distribution statement after review. No release approval is claimed by this draft.")
    add(root, "metainfo/metd", "20260913")
    add(root, "metainfo/metc/cntinfo/cntorgp/cntorg", "REVIEW_REQUIRED responsible metadata organization")
    add(root, "metainfo/metc/cntinfo/cntemail", "REVIEW_REQUIRED shared group email")
    add(root, "metainfo/metstdn", "FGDC Content Standard for Digital Geospatial Metadata")
    add(root, "metainfo/metstdv", "FGDC-STD-001-1998")
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def validate(tables):
    dep = tables["deployments"]
    assert not dep.duplicated(["season", "deployment_id"]).any()
    assert dep.latitude.between(34, 35).all() and dep.longitude.between(-121, -120).all()
    keys = set(zip(dep.season, dep.deployment_id))
    photos = tables["photo_index"]
    assert not photos.duplicated(["season", "deployment_id", "image_filename"]).any()
    for name in ("photo_index", "classifications", "temperature_measurements", "wind_measurements"):
        frame = tables[name]
        assert set(zip(frame.season, frame.deployment_id)) <= keys, name
    photo_keys = set(zip(photos.season, photos.deployment_id, photos.image_filename))
    for name in ("classifications", "temperature_measurements"):
        frame = tables[name]
        assert set(zip(frame.season, frame.deployment_id, frame.image_filename)) <= photo_keys, name
    wind = tables["wind_measurements"]
    assert not wind.duplicated().any()
    linked = wind.merge(dep[["season", "deployment_id", "start_time_recorded", "end_time_recorded"]], on=["season", "deployment_id"], validate="many_to_one")
    time = pd.to_datetime(linked.timestamp_recorded, format="mixed")
    assert time.ge(pd.to_datetime(linked.start_time_recorded, format="mixed")).all()
    assert time.le(pd.to_datetime(linked.end_time_recorded, format="mixed")).all()
    classification = tables["classifications"]
    assert classification.sun_exposed_butterfly_index.le(classification.butterfly_index).all()
    thirty = tables["analysis_30_minute"]
    classified = set(classification.image_filename)
    analysis_images = set(thirty.previous_image_filename) | set(thirty.current_image_filename)
    assert {("2023-2024", f.rsplit("_", 1)[0], f) for f in analysis_images} <= photo_keys
    missing = sorted(analysis_images - classified)
    values = classification.set_index("image_filename").butterfly_index
    for prefix in ("previous", "current"):
        found = thirty[f"{prefix}_image_filename"].isin(values.index)
        np.testing.assert_allclose(thirty.loc[found, f"{prefix}_bi"], thirty.loc[found, f"{prefix}_image_filename"].map(values))
    return dict(table_rows={name: len(frame) for name, frame in tables.items()},
                analysis_images_without_classification=missing,
                schema_and_join_checks="passed", raw_data_modified=False, clock_corrections_applied=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("/Volumes/MonarchSSD/data_release"))
    parser.add_argument("--reconciliation", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/release")
    parser.add_argument("--package-dir", type=Path)
    parser.add_argument("--analysis-only", action="store_true", help="Rebuild the two analysis CSVs without the portable drive")
    args = parser.parse_args()
    tables = {
        "analysis_30_minute": analysis_30_minute(pd.read_csv(ROOT / "data/monarch_analysis_lag30min.csv")),
        "analysis_next_day": analysis_next_day(pd.read_csv(ROOT / "data/monarch_daily_lag_analysis_nextday_window.csv")),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.analysis_only:
        for name, frame in tables.items():
            frame.to_csv(args.output_dir / f"{name}.csv", index=False)
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
    wind = wind.merge(dep[["season", "deployment_id"]], on=["season", "deployment_id"], validate="many_to_one")
    wind = wind[["season", "deployment_id", "wind_sensor_name", "timestamp_recorded", "wind_speed_m_s", "wind_gust_m_s", "wind_direction_degrees"]]
    tables = dict(deployments=dep, photo_index=photos, classifications=classifications(dep), temperature_measurements=temp, wind_measurements=wind, **tables)
    validation = validate(tables)
    fields = dictionary(tables)
    xml = metadata_xml(tables, fields)
    readme = "# Monarch monitoring data release draft\n\n" + "\n\n".join(f"{name}.csv. {TABLES[name]} Contains {len(frame):,} rows." for name, frame in tables.items())
    readme += "\n\n" + CLOCK_NOTE + "\n\n" + FILENAME_NOTE + "\n\n" + WIND_NOTE
    readme += "\n\nCoordinates are longitude and latitude in WGS84, EPSG 4326, expressed in decimal degrees. Later camera coordinates were transformed from EPSG 3498. First-season source geometries were already EPSG 4326. They represent camera positions, not separate wind-meter positions. Coordinate precision does not establish positional accuracy.\n\n"
    readme += "Missing CSV values are empty fields. Join observations using season and deployment_id. SC12 occurs in both seasons. Retain the season when combining tables. Only the analysis tables omit season because they contain first-season data exclusively. Wind observations shared by SC9 and SC10 must not be counted as independent measurements.\n\n"
    readme += "The temperature table preserves the previously reviewed overlay values. No second-season temperature extraction or butterfly classification was supplied. Review deployment data_quality_note before using wind. UDMH1 has source-reported corruption. PS01 stops before the camera stops. SC12 has a long gap followed by zero-valued January records of uncertain context. No gap filling or new sensor corrections were performed.\n\n"
    readme += "The analysis CSVs are renamed, reduced copies of the historical manuscript inputs. They do not recompute weather summaries from the broader reconciled wind archive. That archive includes additional deployments and preserves exact source boundary seconds. Analysis reproduction and re-derivation from the broader observational archive are distinct operations. The time covariate is minutes since the first daily observation, not calculated astronomical sunrise.\n\n"
    if validation["analysis_images_without_classification"]:
        readme += "Pending classification review. The historical analysis includes " + ", ".join(validation["analysis_images_without_classification"]) + ", an unconfirmed all-zero source record with no observer. It is omitted from classifications as an unclassified placeholder. The historical analysis value is preserved pending an explicit decision about reanalysis. Other unconfirmed records are retained only where saved annotations or a saved user provide evidence of classification.\n\n"
    readme += "data_dictionary.csv defines every data column. metadata.xml is a draft with explicit REVIEW_REQUIRED fields. Release author order, DOI, USGS metadata identifier, shared contact, distribution terms and final approval must be supplied before publication. XML well-formedness alone is not FGDC validation.\n\n"
    readme += "Analysis scripts remain at https://github.com/kylenessen/monarch-wind-light-manuscript. Use the release CSVs with the matching repository version. Run Rscript analysis/run_results_analyses.R from that repository root. A final public commit link must be pinned before distribution. Scripts are not included in this package.\n\n"
    readme += "The local staging package uses directory links for photos to avoid copying the full archive. Before upload, create ordinary photo archives containing only the JPEG paths listed in photo_index.csv, preserving photos/season/deployment_id/ paths. Do not distribute symbolic links or unlisted source files.\n"
    package = args.package_dir or args.archive / "publication_package"
    for destination in (args.output_dir, package):
        destination.mkdir(parents=True, exist_ok=True)
        for name, frame in tables.items():
            frame.to_csv(destination / f"{name}.csv", index=False, na_rep="", lineterminator="\n")
        fields.to_csv(destination / "data_dictionary.csv", index=False, na_rep="")
        (destination / "metadata.xml").write_bytes(xml)
        (destination / "README.md").write_text(readme)
    for row in dep.itertuples(index=False):
        source = args.archive / ("raw/Camelot_Photos" if row.season == "2023-2024" else "VSFB_2025_Deployment_Review") / row.deployment_id
        if not source.is_dir():
            continue
        target = package / "photos" / row.season / row.deployment_id
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.symlink_to(source, target_is_directory=True)
        elif target.resolve() != source.resolve():
            raise ValueError(f"Existing photo link points to a different source {target}")
    (ROOT / "data/release_working/validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    print(json.dumps(validation, indent=2))
    print(f"Public staging package {package}")


if __name__ == "__main__":
    main()
