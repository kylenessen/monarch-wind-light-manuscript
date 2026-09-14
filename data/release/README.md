# Monarch monitoring data release draft

deployments.csv. One row per season and camera deployment, including identifiers, WGS84 location, boundaries and known limitations. Contains 28 rows.

photo_index.csv. One row per retained JPEG photograph. Links images to the deployment table and collection folders. Contains 223,887 rows.

classifications.csv. One row per image with evidence of classification, with ordinal cell primitives and BI totals. Unclassified placeholders are omitted. Covers the first season only. Contains 8,299 rows.

temperature_measurements.csv. One row per reviewed first-season image-overlay temperature record, including missing temperature values. No second-season temperature extraction was supplied. Contains 56,066 rows.

wind_measurements.csv. One row per distinct wind observation associated with an assigned deployment interval. Identical observations within an instrument are deduplicated. SC9 and SC10 share StarDust observations because both deployment records assign that sensor during overlapping intervals. These shared rows are not independent measurements. Contains 757,260 rows.

analysis_30_minute.csv. Retained 30-minute manuscript input, with only variables used by the primary analyses, descriptive summaries and focused observer sensitivity. Both-zero BI pairs were excluded upstream. Photo-pair tolerance is five minutes. Row order and values are preserved. Contains 1,894 rows.

analysis_next_day.csv. Retained next-day manuscript input after >=95 percent overall coverage and complete-case selection. Deployment-days contain 15-25 daytime observations, consecutive days are paired, and pairs with both daily maxima zero are excluded. Coverage is the geometric mean of temperature, wind and daylight-image coverage. Source observation-order gaps are preserved. Signed square-root delta BI is calculated in R. Contains 96 rows.

Camera and wind-meter clocks do not automatically apply daylight saving time. For the 2024-2025 season, timestamps remain on the recorded device clocks. No daylight saving or UTC conversion was applied to either series during release preparation. Apparent image lighting and civil clock time may therefore differ by one hour. Repeated clock times identify distinct photos and are retained. The investigator reports accounting for seasonal clock changes during first-season processing, but the exact historical procedure has not been recovered. Existing first-season timestamps are preserved. No UTC offset or independently verified camera-to-logger synchronization is asserted.

Photographs are grouped in photos/season/deployment_id/. Image filenames use deployment_id_YYYYMMDDHHMMSS.JPG, corresponding to the format code %Y%m%d%H%M%S. The deployment identifier may itself contain an underscore. The timestamp has a four-digit year followed by two-digit month, day, 24-hour hour, minute and second. It carries no timezone. For the reviewed second season it comes from the photo EXIF capture time. Existing first-season canonical filenames are preserved. Distinct second-season photos sharing a timestamp use the unsuffixed name and an _02 suffix before .JPG. This suffix is a collision counter, not a fractional second, ordering guarantee, or clock correction. The photo index links every released filename to its deployment folder. One collection-level description applies to all images in each deployment folder. Individual photo metadata records are not required.

Wind speed and gust are in meters per second. Direction is reported in degrees clockwise from north, with 360 representing north. The instrument manual specifies a 16-point sensor with 22.5-degree resolution and averaged logging. The database contains integer directions throughout 0 to 360, so exported observations are not restricted to 45-degree increments. The investigator considers direction 0 invalid or suspect. That interpretation has not been confirmed in the manufacturer manual, so original zeros are retained and should not be treated as confirmed north. Blank is missing. Zero speed or gust is not automatically invalid. Manual https://rainwise.com/downloads/windsoft/WindLog140805%20.pdf, section 7.2. Matching source databases use Units code 2, consistent with the manuscript m/s convention.

Coordinates are longitude and latitude in WGS84, EPSG 4326, expressed in decimal degrees. Later camera coordinates were transformed from EPSG 3498. First-season source geometries were already EPSG 4326. They represent camera positions, not separate wind-meter positions. Coordinate precision does not establish positional accuracy.

Missing CSV values are empty fields. Join observations using season and deployment_id. SC12 occurs in both seasons. Retain the season when combining tables. Only the analysis tables omit season because they contain first-season data exclusively. Wind observations shared by SC9 and SC10 must not be counted as independent measurements.

The temperature table preserves the previously reviewed overlay values. No second-season temperature extraction or butterfly classification was supplied. Review deployment data_quality_note before using wind. UDMH1 has source-reported corruption. PS01 stops before the camera stops. SC12 has a long gap followed by zero-valued January records of uncertain context. No gap filling or new sensor corrections were performed.

The analysis CSVs are renamed, reduced copies of the historical manuscript inputs. They do not recompute weather summaries from the broader reconciled wind archive. That archive includes additional deployments and preserves exact source boundary seconds. Analysis reproduction and re-derivation from the broader observational archive are distinct operations. The time covariate is minutes since the first daily observation, not calculated astronomical sunrise.

Investigator review retained SC1_20231120133001.JPG as a valid zero-BI classification and assigned Skyler as primary observer, following the majority of SC1 classifications. All 752 source SC1 records with a saved user identify SM, and the deployment metadata names Skyler. The original software confirmation flag remains false and the original record_user_id remains blank. The release assignment is in primary_observer. The original JSON and historical analysis values are unchanged.

data_dictionary.csv defines every data column. metadata.xml is a draft with explicit REVIEW_REQUIRED fields. Release author order, DOI, USGS metadata identifier, shared contact, distribution terms and final approval must be supplied before publication. XML well-formedness alone is not FGDC validation.

Analysis scripts remain at https://github.com/kylenessen/monarch-wind-light-manuscript. Use the release CSVs with the matching repository version. Run Rscript analysis/run_results_analyses.R from that repository root. A final public commit link must be pinned before distribution. Scripts are not included in this package.

The local staging package uses directory links for photos to avoid copying the full archive. Before upload, create ordinary photo archives containing only the JPEG paths listed in photo_index.csv, preserving photos/season/deployment_id/ paths. Do not distribute symbolic links or unlisted source files.
