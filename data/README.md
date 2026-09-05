# Data Directory

This directory contains the source data used to generate the analysis CSV files for the manuscript. The data preparation scripts in `analysis/` combine deployment classifications, deployment metadata, image-derived temperature values, and wind sensor records into the datasets used by the statistical analysis scripts.

The `deployments/` directory contains hand-labeled image classifications in JSON format. The `wind/` directory contains the SQLite databases exported from each wind sensor. The `deployments.csv` file describes deployment metadata, including the camera or wind sensor, deployment location, and deployment duration. The `temperature_data_2023.csv` file contains temperature values extracted from the field images.

The generated datasets for the two analyses retained in the manuscript are `monarch_analysis_lag30min.csv` and `monarch_daily_lag_analysis_nextday_window.csv`. See the [analysis guide](../analysis/README.md) for the scripts and commands used to regenerate the retained datasets and model outputs.

## Classification and Temperature Protocols

The image-classification protocol, including example images and cell-level decision rules, is published at <https://kylenessen.github.io/monarch_trailcam_classifier/>. The deployment JSON files preserve the resulting cell classifications. Each deployment was classified by one labeler, so the data do not support a formal inter-observer agreement estimate.

Camera temperature values were read from image overlays with a custom optical-character-recognition script that used image preprocessing and pattern matching. Deployment-level temperature time series were then plotted, reviewed, and manually corrected for implausible extractions. The reviewed values used by the analysis are preserved in `temperature_data_2023.csv`. The original extraction utility is not part of this repository, and the camera readings were not independently calibrated against reference temperature sensors.

## Data Availability Notes

The raw image files are not included in this repository because of storage constraints. A USGS ScienceBase release containing the original photographs, deployment metadata, image classifications, wind measurements, and reviewed image-derived temperature values used in this study is in preparation and will be made publicly available before publication. The source code for the custom image-classification software is available at <https://github.com/kylenessen/monarch_trailcam_classifier>.

Deployments with no butterfly detections are also excluded from this repository. In those cases, the pole location and wind data still exist, but are not included here.

The [draft release tables](release/README.md) provide open-format copies of the source records and a field dictionary. They are a working release product with documented gaps. Use the two analysis CSV files above to reproduce the manuscript with the R scripts.
