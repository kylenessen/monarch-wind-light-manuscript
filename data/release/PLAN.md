# Data release working plan

Started September 9, 2026 on branch `data-release`. The initial inventory below describes repository commit `f5857fe`. This is a working plan for the broader release, separate from the descriptions of the current draft products in [README.md](README.md).

## Agreed scope

Release all available study photographs, wind records, reviewed temperature records, and supporting deployment information from both seasons. Include deployments and observations that were not used in the manuscript, including deployments without butterfly detections. Make the observations useful for independent reuse. Include compact analysis CSVs for the two retained manuscript results.

Photograph preparation, particularly the unprocessed second season, is being handled in a separate task. Coordinate using its deployment mapping and image manifest. Unprocessed photographs do not imply zero butterflies or completed classifications. The reviewed temperature source already exists and does not need another extraction pass for this initial work.

The preferred wind product is one CSV connecting wind measurements to deployment IDs. SQLite databases remain source inputs. The public wind product must account for all source records, including records outside the deployment intervals currently available in this repository.

## Existing work

The release was already documented in [the data availability notes](../README.md) and [the draft release README](README.md). Commit `81cd4c6` added normalized source tables on September 3, 2026. Commit `497d974` added the analysis tables, release README, and dictionary the same day. [The preparation script](../../analysis/prepare_data_release.py) generates the seven draft CSVs. [The photograph export guide](../../tools/README.md) documents a separate export utility with a deployment mapping and image manifest.

The checked-in draft tables have the following sizes. Counts use CSV parsing, so multiline deployment notes count as part of one record.

| Product | Records | Columns | Current purpose |
| --- | ---: | ---: | --- |
| `deployments.csv` | 12 | 15 | Available deployment metadata |
| `classifications.csv` | 11,885 | 17 | Image classifications and category counts |
| `temperature_measurements.csv` | 56,066 | 6 | Reviewed image-derived temperatures |
| `wind_measurements.csv` | 310,342 | 6 | Wind records within listed deployment intervals |
| `analysis_30_minute.csv` | 1,894 | 19 | Trimmed 30-minute analysis inputs |
| `analysis_next_day.csv` | 96 | 23 | Trimmed next-day inputs passing the completeness threshold |
| `data_dictionary.csv` | 86 | 6 | Field descriptions, units, and observed ranges |

Every column in the six data products has an entry in the current dictionary. This establishes dictionary coverage, not that every definition or analysis field has passed scientific review. The README gives brief file descriptions. No release metadata XML was found among tracked repository files.

## Wind inventory and assignment gaps

The 11 SQLite databases contain 681,013 rows in their `Wind` tables. The audit opened databases read-only and compared each sensor's records with all its listed deployment intervals. It reproduced the exporter's inclusive interval comparison and its truncation of interval boundaries to whole seconds. Counts below refer to source database rows, before duplication across deployments.

| Source database | Source records | Within at least one listed interval | Outside listed intervals |
| --- | ---: | ---: | ---: |
| `BlueLake.s3db` | 73,182 | 72,970 | 212 |
| `FoxTrail.s3db` | 3,059 | 2,829 | 230 |
| `FunStorm.s3db` | 74,841 | 30,311 | 44,530 |
| `JazzPlay.s3db` | 40,314 | 40,241 | 73 |
| `JoyHouse.s3db` | 180,009 | 940 | 179,069 |
| `MoonTide.s3db` | 72,617 | 52,480 | 20,137 |
| `OakTrust.s3db` | 25,688 | 0 | 25,688 |
| `PugSnore.s3db` | 86,525 | 0 | 86,525 |
| `StarDust.s3db` | 86,783 | 79,025 | 7,758 |
| `SunRuler.s3db` | 18,978 | 0 | 18,978 |
| `TreeTalk.s3db` | 19,017 | 0 | 19,017 |
| Total | 681,013 | 278,796 | 402,217 |

The existing CSV has 310,342 rows because 31,546 StarDust records match both SC9 and SC10. Those deployments have overlapping intervals ending January 31, 2024. Establish whether this represents an intentionally shared sensor or incorrect metadata before deciding the release row structure. A source record identifier will let readers recognize a shared measurement if multiple deployment associations are valid.

The source schema contains `id`, `time`, `speed`, `gust`, and `direction`. The current export drops the database row ID. Preserve source provenance in the expanded export, using a stable source database identifier together with the source row ID after verifying its uniqueness. Inspect duplicate timestamps without assuming they are duplicate measurements. Do not silently discard or aggregate records.

Some databases contain timestamps in 2008. JoyHouse contains timestamps extending into July 2025. These dates need review and do not establish valid study coverage or second-season provenance. Verify sensor clock conventions, deployment boundaries, and any corrections against field records. The current README's PST convention applies to the draft coverage and should not automatically be extended to every source record.

Retain unmatched or ambiguous records during preparation with an explicit assignment status. Resolve deployment IDs from authoritative field metadata rather than guessing from nearby observations. If some records cannot be assigned, document that limitation while retaining them in the release. The aim remains a single wind CSV, with the row structure settled after reviewing shared sensors.

## Other known gaps

Six temperature deployment IDs are absent from the current deployment table. They are SC3, SC5, SC11, SLC6_1, UDMH1, and UDMH3. This was confirmed against the checked-in temperature release table. Recover their deployment metadata without reprocessing the reviewed temperature values.

The existing release README reports five images used in the 30-minute manuscript input as unconfirmed in the source classification JSON. That finding needs review before finalization. The current draft does not include the second-season photo archive or its complete deployment metadata. Existing wind databases may contain additional periods, as the inventory above shows, but their relationship to the second season has not been established.

## Next work

First locate the complete deployment records and all wind databases for both seasons, including deployments without butterfly detections. Record source identities, sensor names, date ranges, and checksums. Reconcile the photograph task's deployment mapping with these records. The external archive locations and authoritative deployment metadata source still need to be identified.

Then extend the wind exporter to retain source identity, preserve every record, and report missing or multiple deployment matches. Reconcile exported records to the source inventory. Confirm units, direction convention, timestamp precision, clock behavior, and interval boundaries from instrument and field documentation. Preserve the original values alongside any justified corrections and document the changes.

Review the two existing analysis tables against the final manuscript model scripts. Keep the identifiers, responses, predictors, and fields needed to reproduce selection rules and model structure. Remove unused fields only after checking those dependencies. The current tables are already trimmed and provide the starting point.

Complete documentation for each file and each field. Record what one row represents, join keys, units, missing-value conventions, allowed flag values, time conventions, spatial reference, measurement methods, processing steps, coverage, and known limitations. Link images through a manifest with stable names and deployment IDs. Document which photographs have classifications and which do not. Verify the applicable ScienceBase and USGS metadata and review requirements before preparing the final submission package. This plan does not establish compliance with those requirements.

Finish by validating joins across products, accounting for all source records and image files, checking the dictionary against every released column, and reproducing both manuscript analyses from the release inputs. Record package checksums and the exact code revision used to build it.
