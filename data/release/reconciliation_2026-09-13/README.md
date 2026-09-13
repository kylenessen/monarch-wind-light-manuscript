# Reviewed photographs and reconciled wind

Prepared September 13, 2026 after the user completed photograph review. The user authorized returning all remaining review images to the main deployment folders, removing the remaining 2022-dated SC12 image, using the 2025 photographs to define wind intervals, and excluding unrelated observations from an overlapping Pismo wind study.

The complete outputs are in `/Volumes/MonarchSSD/data_release/reconciled_2026-09-13`. This repository directory preserves the small summaries and field definitions. The large wind table, source-row links, image manifest, and removed-file accounting remain on the portable drive.

The user subsequently excluded AIR1 / VEXX from the current release because its photographs are unavailable. The decision is stored in `../deployment_exclusions.json` and honored by both preparation scripts. Active interval and coverage tables now contain 28 deployments. [FIELD_INTERPRETATION.md](FIELD_INTERPRETATION.md) records the evidence for shared SC9/SC10 wind and the incomplete second-season recording sequences.

## Photographs

All 60 remaining review images were renamed and returned to their deployment folders. They were distinct photographs in five deployments with repeated November 3 timestamps. The first occurrence uses `deployment_YYYYMMDDHHMMSS.JPG`. The second uses `deployment_YYYYMMDDHHMMSS_02.JPG`. No timestamp or image-content changes were made. The suffix distinguishes filenames without inventing a capture time. The move journal records the original and current paths and verified SHA-256 values.

The user specifically requested removing `SC12/SC12_20220910153432.JPG` from the cleaned set. Its checksum and reason are recorded in `photo_removed_by_request.json`. Original raw photographs were not changed.

The cleaned export contains 167,821 JPEGs across nine deployments. AIR1, camera VEXX, has no photographs. There are 8,482 fewer files than the original 176,303-file export, including the user's cleanup and the one requested removal. This difference includes non-JPEG media as well as photographs. No review files remain. The current EXIF time was read from every retained JPEG. All final filenames agree with those times. No date segmentation or timezone correction was applied.

`reviewed_image_manifest.csv` describes the current set. The September 10 inventory remains an unmodified historical export record. The new manifest uses previously verified export hashes for 167,761 files whose size and modification time still match. The 60 renamed images were rehashed. This run did not rehash the entire archive.

## Wind selection and deduplication

The pipeline inspected 92 databases, comprising 11 repository sources and 81 files in the portable raw archive. First-season sensor assignments and exact deployment/recovery boundaries come from the 19-record deployment GeoPackage. Second-season sensor assignments come from the camera snapshot. Their intervals are the earliest and latest EXIF timestamps in each cleaned photo set, as instructed by the user.

Matching requires both the assigned sensor and an inclusive recorded-time interval. It is not a global calendar filter. Database names are matched case-insensitively. The single explicit filename alias maps `OC SW CatFable` to `CatFable`. The alias does not admit its older records into the second season. The separate Weather Underground database is not a WindLog source and is not included in this product.

The script reads candidate databases into pandas, normalizes timestamp formatting and numeric whitespace, retains matching rows, concatenates them, and removes exact measurement duplicates. The identity consists of sensor, timestamp, speed, gust, and direction. Database row IDs do not define measurement identity across files. Source paths and row IDs remain in a separate provenance table. Different instruments remain distinct even when their values agree. Conflicting measurements at the same sensor and timestamp would be retained and flagged. None were found among the retained records.

| Accounting measure | Count |
| --- | ---: |
| Source database rows, including repeated copies | 11,697,325 |
| Rows outside the assigned sensor and interval rules | 9,897,344 |
| Matching source rows before deduplication | 1,799,981 |
| Duplicate measurement copies removed | 1,074,267 |
| Distinct retained measurements | 725,714 |
| First-season distinct measurements | 500,391 |
| Second-season distinct measurements | 225,323 |
| Rows in the deployment-linked wind CSV | 757,260 |
| Additional associations for the shared SC9/SC10 sensor | 31,546 |
| Conflicting distinct measurements | 0 |

SC9 and SC10 have overlapping StarDust assignments in the source metadata. Each applicable deployment therefore receives a row, with the same measurement ID linking the shared observation. These additional associations are not duplicate sensor readings. The original shared-sensor interpretation remains a source-metadata issue, and the release makes the relationship explicit.

`deployment_key` combines season and original deployment ID. Thus `2023-2024/SC12` and `2024-2025/SC12` are distinct without renaming the source identifiers or photograph folders.

## Second-season coverage

| Deployment | Camera | Assigned sensor | Retained wind observations |
| --- | --- | --- | --- |
| PS01 | EM03 | JoyHouse | 149,009, from October 19, 2024 at 14:07 through January 31, 2025 at 04:04 |
| SC12 | IRIS | RockWall | 76,314, from October 31, 2024 at 12:51 through January 14, 2025 at 22:01 |
| MM01 | NOVA | LeafWind | Files found, no records inside the photo interval |
| SLC6_3 | KIWI | BarkRoar | File found, no records inside the photo interval |
| TGR2 | MOSS | CatFable | File found, no records inside the photo interval |
| CR01 | GOLD | VineLoop | No matching database found |
| UDMH05 | JADE | LeftLion | No matching database found |
| BC01 | APEX | EchoBuzz | No matching database found |
| ARC1 | ORCA | BoltZoom | No matching database found |

Available wind spans end before the cleaned photo spans for PS01 and SC12. The reports describe available observations, not full coverage. In particular, SC12's regular sequence stops December 23. Its January 14 endpoint consists of 69 zero-valued records after a 22-day gap and may reflect a later connection or test. See the field interpretation before treating those rows as continued field recording. The source deployment notes identify corrupted wind data at first-season UDMH1. Its 18,922 in-window records are retained with a quality note rather than being treated as validated readings.

The recorded clocks are compared directly, as in the existing first-season scripts. Repeated photo timestamps show that timezone labels cannot simply be generalized to all sources. The new fields say `timestamp_recorded`, and no UTC alignment or clock correction is claimed. All matched wind databases have Units code 2, the same as the manuscript source databases. Numeric wind values retain the existing release's meters-per-second and degree conventions.

The new first-season filter retains fractional seconds in the GeoPackage boundaries. The old draft exporter truncated them. Consequently, nine old draft rows at the whole second immediately before a deployment start do not pass this stricter filter. All nine differences are recorded in `validation.json`. The original manuscript inputs and draft CSVs have not been overwritten.

## Files on the portable drive

| File | Purpose |
| --- | --- |
| `wind_measurements.csv` | One distinct measurement association per season and deployment, with shared measurement IDs and quality flags. |
| `wind_record_sources.csv` | Links each retained measurement to every corresponding original database row. |
| `wind_source_inventory.csv` | Source checksums, row accounting, raw timestamp ranges, sensor matching, and device settings. |
| `deployment_intervals.csv` | The 28 active first- and second-season filtering records. AIR1 is excluded. This is not a full replacement spatial deployment table. |
| `deployment_wind_coverage.csv` | Counts, coverage endpoints, and explicit reasons for missing wind data. |
| `wind_timestamp_conflicts.csv` | Conflict report. Currently contains headers and no records. |
| `reviewed_image_manifest.csv` | Current files linked to original paths, EXIF times, and checksums. |
| `removed_after_review.csv` | Original export files absent from the cleaned collection. |
| `photo_intervals_2025.csv` | Earliest and latest current photo timestamps per deployment. |
| `data_dictionary.csv` | Definitions for all 88 fields across the nine CSV products above. |
| `photo_rename_plan.json` | Resumable journal of the 60 verified renames. |
| `photo_removed_by_request.json` | Record of the specific user-authorized SC12 deletion. |
| `photo_summary.json` and `wind_summary.json` | Totals, rules, source identities, and coverage summaries. |
| `validation.json` | Independent checks and the nine explained differences from the old draft. |
| `source_metadata/` | Frozen copies of the first-season deployment and second-season camera GeoPackages used for this run. |
| `deployment_exclusions.json` | User-authorized omissions from the active release. Source records remain preserved. |

## Reproduction and validation

The preparation scripts are [finalize_reviewed_photos.py](../../../tools/finalize_reviewed_photos.py) and [reconcile_release_wind.py](../../../tools/reconcile_release_wind.py). Run with `uv run`. The first operates on the reviewed export and preserves its original inventory. Its rename journal supports safe resumption. The second opens all source databases read-only and writes new output CSVs.

From the data-release worktree, the wind command used was:

```sh
uv run tools/reconcile_release_wind.py \
  --repo /Users/kylenessen/.codex/worktrees/0dbf/monarch-wind-light-manuscript \
  --raw /Volumes/MonarchSSD/data_release/raw \
  --photo-intervals /Volumes/MonarchSSD/data_release/reconciled_2026-09-13/photo_intervals_2025.csv \
  --deployments-gpkg /Volumes/MonarchSSD/data_release/reconciled_2026-09-13/source_metadata/deployments_2024.gpkg \
  --cameras-gpkg /Volumes/MonarchSSD/data_release/reconciled_2026-09-13/source_metadata/cameras_2025.gpkg \
  --output /Volumes/MonarchSSD/data_release/reconciled_2026-09-13
```

The archived metadata copies have the same bytes as the original paths recorded in the initial run summary. A rerun with these paths changes only the recorded source locations.

Six focused tests passed for safe photo moves, interrupted-operation recovery, duplicate handling, conflicting measurements, missing values, and exact interval boundaries. Independent checks on the written CSVs verified assigned sensors, inclusive bounds, uniqueness, complete source links, source counts, and photo filename agreement with current EXIF times. Dictionary coverage was checked against every output CSV header.

This is the completed photo and wind reconciliation step. Final release metadata, full spatial deployment tables, the remaining missing wind sources, and validation of manuscript reproduction from the assembled release remain separate work.
