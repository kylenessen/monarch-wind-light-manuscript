# Data Directory

This directory contains the source data used to generate the analysis CSV files for the manuscript. The data preparation scripts in `analysis/` combine deployment classifications, deployment metadata, image-derived temperature values, and wind sensor records into the datasets used by the statistical analysis scripts.

The `deployments/` directory contains hand-labeled image classifications in JSON format. The `wind/` directory contains the SQLite databases exported from each wind sensor. The `deployments.csv` file describes deployment metadata, including the camera or wind sensor, deployment location, and deployment duration. The `temperature_data_2023.csv` file contains temperature values extracted from the field images.

The historical analysis inputs are `monarch_analysis_lag30min.csv` and `monarch_daily_lag_analysis_nextday_window.csv`. The R analysis now reads their reduced, renamed versions in [analysis_inputs/analysis_30_minute.csv](analysis_inputs/analysis_30_minute.csv) and [analysis_inputs/analysis_next_day.csv](analysis_inputs/analysis_next_day.csv). See the [analysis guide](../analysis/README.md) for regeneration and validation commands.

## Classification and Temperature Protocols

The image-classification protocol, including example images and cell-level decision rules, is published at <https://kylenessen.github.io/monarch_trailcam_classifier/>. The deployment JSON files preserve the resulting cell classifications. Each deployment was classified by one labeler, so the data do not support a formal inter-observer agreement estimate.

Camera temperature values were read from image overlays with a custom optical-character-recognition script that used image preprocessing and pattern matching. Deployment-level temperature time series were then plotted, reviewed, and manually corrected for implausible extractions. The reviewed values used by the analysis are preserved in `temperature_data_2023.csv`. The original extraction utility is not part of this repository, and the camera readings were not independently calibrated against reference temperature sensors.

## Data Availability Notes

The raw image files are not included in this repository because of storage constraints. The [USGS data release](https://doi.org/10.5066/P13IEKEB) by Nessen, Ibsen, Diffendorfer and Villablanca (2026) contains the photographs, deployment metadata, image classifications, wind measurements, and reviewed image-derived temperature values. The source code for the custom image-classification software is available at <https://github.com/kylenessen/monarch_trailcam_classifier>.

The expanded release tables include available deployment and weather records outside the manuscript subset, including deployments with no butterfly detections. Unclassified photos do not establish absence. The observational release includes both field seasons. The classification summary and reviewed temperatures cover the first season. Native classification JSON files remain in this repository and are not release attachments. Manuscript analysis inputs remain separately in analysis_inputs/.

The [draft release tables](release/README.md) include a photo index, field dictionary and draft metadata XML. The separate [working notes](release_working/STATUS.md) record provenance, verification and remaining decisions. Working notes and scripts are not data-release attachments. Recorded device clocks are preserved except for TGR1 photo times, reconstructed from deployment start and end. The visible TGR1 overlays retain the original camera timestamps.
