# Data Directory

This directory contains the source data used to generate the analysis CSV files for the manuscript. The data preparation scripts in `analysis/` combine deployment classifications, deployment metadata, image-derived temperature values, and wind sensor records into the datasets used by the statistical analysis scripts.

The `deployments/` directory contains hand-labeled image classifications in JSON format. The `wind/` directory contains the SQLite databases exported from each wind sensor. The `deployments.csv` file describes deployment metadata, including the camera or wind sensor, deployment location, and deployment duration. The `temperature_data_2023.csv` file contains temperature values extracted from the field images.

The generated analysis datasets are also stored here. These include `monarch_analysis_lag30min.csv`, `monarch_daily_lag_analysis_24hr_window.csv`, and `monarch_daily_lag_analysis_nextday_window.csv`. See `analysis/README.md` for the scripts and commands used to regenerate these files.

## Data Availability Notes

The raw image files and the software used to view and edit classifications are not included in this repository because of storage constraints. They can be provided separately, but a long-term public hosting location has not yet been established.

Deployments with no butterfly detections are also excluded from this repository. In those cases, the pole location and wind data still exist, but the deployment-level classification files are not included here.
