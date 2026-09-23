# Current status

Updated September 22, 2026. The completed data-release branch has been merged into main. The repository release tables now match the canonical package at /Volumes/MonarchSSD/data_release/publication_package, including the final reviewed metadata, dictionary and NULL values. Native classification JSON files remain in data/deployments and are not release attachments. The current classification summary contains 3,713 records.

Peter supplied the release citation and DOI, [10.5066/P13IEKEB](https://doi.org/10.5066/P13IEKEB), with publication date September 30, 2026. The manuscript now cites the release first in the data availability statement and includes it in the bibliography. The local metadata XML remains the September 16 review snapshot. See the [approval record](../../research/usgs-manuscript-approval-2026-09-16.md) and [release review record](../../research/data-release-review-2026-09-16.md). The release builder predates the final manual metadata and missing-value edits, so a rebuild requires reapplying those reviewed changes.

The September 14 record below is historical and is superseded by this update where they differ.

# Data release status

Updated September 14, 2026. Work is on the data-release branch. The current package
is /Volumes/MonarchSSD/data_release/publication_package. data/release contains the
matching tables and documentation. Its generated JSON copies are not duplicated
in Git because their source files are already tracked in data/deployments.

The observational release contains deployments, photographs and their index, wind
measurements, reviewed camera-overlay temperatures, native classification JSON,
a classification summary CSV, a data dictionary and metadata XML. It covers both
seasons. Classifications and reviewed temperatures cover the first season.

The two manuscript analysis tables are in data/analysis_inputs. The R scripts read
them there. Their values are unchanged. They are not data-release attachments.
The earlier numerical comparison is preserved in analysis_verification.json.

Both seasons use the same public fields and photos/deployment_id/ paths.
Camera and wind instrument fields are camera_id and wind_sensor_id. Measurement
column names omit unit suffixes. Units are recorded in the data dictionary.
Observation date and time columns are named timestamp. Deployment
times are named start_time and end_time and displayed as YYYY-MM-DD HH:MM:SS.
The classification summary retains saved user identifiers and daytime annotations,
including unconfirmed records. Night rows and the confirmation and night columns
are omitted. Native JSON files retain the full annotations. The release
retains one photograph per deployment and capture timestamp. Thirty additional
exposures sharing timestamps were excluded at the investigator's request. Their
originals remain in the source archive. Locations are approximate cellphone GPS
positions recorded under canopy, with some points adjusted against satellite imagery.
Times
are described as recorded by the devices, without UTC offsets. TGR1 photo times are reconstructed from deployment
start and end times. Available wind readings within assigned deployment intervals are
included as recorded. Shared SC9 and SC10 observations remain linked to both
deployments.

The 2,973 TGR1 photographs are included with reconstructed EXIF times and canonical
filenames. Elapsed camera intervals were aligned to both deployment endpoints after
removing the 31-day calendar jump. Recording gaps are retained. The visible overlay
keeps the original incorrect camera timestamp. Corrected copies are stored under
/Volumes/MonarchSSD/data_release/corrected_photos/TGR1. Original photos remain in
raw/Unusual Deployments/TGR1. tools/prepare_tgr1_photos.py reproduces the corrected
copies, and tgr1_photo_times.csv records their source filenames and time mapping.

The current package contains 28 deployments, 226,830 photographs, 757,260 wind
associations, 56,066 temperature records, 8,299 classification summaries and 12
native classification JSON files. The builder's existing schema and join checks
passed. No software-loading check or statistical model rerun was performed for
this packaging change.

Photo folders in the local package use links to existing files. Final upload
archives must contain ordinary JPEG files selected by photo_index.csv and preserve
their deployment paths. The release DOI, metadata identifier, institutional contact
and distribution terms remain to be completed with USGS. A fixed public repository
version should be cited when the release is published.

Earlier reconciliation reports and dated preview or coauthor documents are
historical working materials. They may describe the previous scope. The current
package README and metadata define the present release.
