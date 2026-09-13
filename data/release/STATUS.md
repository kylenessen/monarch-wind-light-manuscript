# Data release status

Updated September 13, 2026 after the user completed photograph review. The 2025 photo set has been finalized at 167,821 images. Wind sources have been merged, deduplicated, and filtered by assigned sensor and deployment interval. There are 725,714 distinct retained measurements and 757,260 deployment-linked rows. The [reconciliation report](reconciliation_2026-09-13/README.md) records the completed work, available outputs, exact rules, and remaining gaps. Full spatial deployment products, missing wind sources, final documentation, and release validation remain unfinished. This investigation did not check a live ScienceBase submission or USGS approval system.

The supplied Pismo XML has been inspected strictly as a structural example. [METADATA_REVIEW.md](METADATA_REVIEW.md) records its section mapping, draft descriptive text, and current USGS guidance. No submission XML has yet been finalized. The new image manifest accounts for the user's cleanup and the 60 subsequent renames. The older observations below document the initial investigation and are superseded where the reconciliation report provides newer results.

## Where the work lives

The task named Start data release branch owns branch `data-release` in `/Users/kylenessen/.codex/worktrees/0dbf/monarch-wind-light-manuscript`. Its last implementation-era commit is `d663c5a`, dated September 9. It contains [PLAN.md](PLAN.md) and [SOURCE_INVENTORY.md](SOURCE_INVENTORY.md). The agreed scope includes both seasons and observations outside the manuscript, including deployments without butterfly detections.

The task named Plan photo renaming workflow worked in the main checkout at `/Users/kylenessen/GitHub/monarch-wind-light-manuscript`. Its later photo export improvements and duration reporting are on `main`, through `77fc748`. The release branch has not incorporated those later tools. The task subsequently moved into camera purchasing research, which obscures the completed photo handoff in its recent conversation.

The live GitHub branch listing still points `main` at `0d10037` and has no `data-release` branch. The four later main commits and release-branch work are local. This status note does not push or merge them.

The portable release workspace is `/Volumes/MonarchSSD/data_release`. Its `raw` directory contains `Camelot_Photos`, `Unusual Deployments`, `VSFB 2025`, `WindLog_laptop`, `updated_wind`, and `wind_data`. Older notes referencing MediaVault do not describe the currently mounted working archive.

## Completed preparation

Seven draft CSVs were created September 3. They include deployments, classifications, reviewed temperatures, wind measurements, the two trimmed manuscript analysis inputs, and a field dictionary. The baseline plan records 56,066 temperature rows, 11,885 classifications, 1,894 thirty-minute analysis rows, and 96 next-day rows. Every current data column has a dictionary entry. These remain draft products covering the existing first-season repository sources.

The QGIS investigation located 19 first-season deployments and 10 later-season camera records in `/Users/kylenessen/GitHub/masters/VSFB_Monarchs`. All six previously missing temperature deployment IDs were found. Those sources have been documented but not imported into the release tables. The first-season intervals would assign another 221,609 records from the repository wind databases, according to the September 9 audit.

The second-season export at `/Volumes/MonarchSSD/data_release/VSFB_2025_Deployment_Review` completed September 10 at 16:03 Pacific time. The job status and SQLite inventory record 176,303 copied files, all with SHA-256 values and no copy errors. This investigation confirmed that every inventoried destination exists. It did not rehash all file contents.

The inventory places 61 files in review-needed paths, comprising 60 timestamp-collision files and one unreadable JPEG. Another 628 files retain their original non-JPEG format. The duration report documents three old 2022 timestamps and no inventoried files for VEXX / AIR1. Export completion therefore does not establish scientific review completion. The user also reported that some cameras may have continued taking photos after takedown. Observed photo endpoints cannot automatically become deployment recovery dates.

## New wind archive findings

The portable drive contains 81 `.s3db` files across `raw/WindLog_laptop` and `raw/updated_wind`. These were absent from the earlier source investigation. Many names occur in both directories. They require comparison with each other and with repository databases before records can be combined.

| Later-season sensor | Located archive evidence |
| --- | --- |
| RockWall | Both directories contain 77,696 rows dated October 30, 2024 through January 14, 2025. This is a candidate later-season source. |
| LeafWind | Both contain 248,883 rows, but the latest recorded timestamp is October 14, 2024, before the camera record creation date. |
| JoyHouse | Both contain 30,928 rows ending January 18, 2024. The repository has a different, larger source that extends into 2025. |
| BarkRoar | WindLog_laptop contains 303 rows ending September 18, 2024. |
| CatFable | WindLog_laptop contains OC SW CatFable.s3db, with 28,034 rows ending November 27, 2023. |
| FireSong | Both contain 74,771 rows ending January 2, 2024. |
| VineLoop, LeftLion, EchoBuzz, BoltZoom | No matching filenames were found in the portable raw archive. |

These checks read the Wind table count and timestamp range. Matching names do not establish correct deployment assignment, equal contents, or valid clocks. Several sources contain 2008 timestamps. The `wind_data` folder also contains `weather_underground_observations.db`, whose relevance has not been assessed.

## Remaining work and recommended order

First reconcile both seasons into a deployment table and identifier crosswalk. SC12 identifies two different deployments across seasons. Later-season camera creation timestamps lack established deployment-start semantics, and recovery dates remain unavailable. Keep separate camera and wind-meter positions and preserve original identifiers.

Next inventory and reconcile all wind sources, retaining source identity and original row IDs. The existing release CSV contains 310,342 rows but represents only 278,796 distinct rows from the 681,013 repository source records. Shared StarDust intervals for SC9 and SC10 cause repeated associations. Importing the fuller first-season metadata improves coverage but does not settle shared sensors, unmatched records, clock anomalies, or second-season completeness.

Then complete photograph review and connect the manifest to the deployment crosswalk. Include the first-season archive and unusual deployments in the final accounting. Preserve distinctions between unclassified images, missing photographs, and confirmed butterfly absences. Review the five manuscript-input images flagged unconfirmed in the existing classification source.

Finally update file descriptions and the dictionary, complete release metadata and review, validate cross-product joins and source accounting, and reproduce both manuscript analyses. The initial September 3 discussion also proposed classifier source and platform builds, raw JSON, and the OCR utility. Their packaging or disposition is not documented as complete and should be settled against the final agreed release scope.

The task named Revise publication hold email last drafted a request on September 9 to hold proofs and publication until USGS internal review was complete, with an estimate of about two weeks. That is evidence of the intended communication, not proof that it was sent or that review has since finished. No completed upload, assigned release DOI, final metadata XML, or approval confirmation was found in the inspected repository and task records.
