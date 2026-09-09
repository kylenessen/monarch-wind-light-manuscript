# Draft USGS Data Release Tables

This directory contains draft open-format tables for the USGS data release associated with the monarch wind and light manuscript. These files are generated from the repository sources by `analysis/prepare_data_release.py`. The source JSON, SQLite databases, and manuscript analysis files remain unchanged.

The [data release working plan](PLAN.md) records the expanded scope for both seasons, including observations not used in the manuscript. It also inventories source wind records omitted by the current deployment filters and identifies overlapping deployment assignments. The tables described here are the existing draft and do not yet cover that expanded scope.

Run the preparation command from the repository root.

```sh
uv run analysis/prepare_data_release.py
```

## Current tables

`deployments.csv` contains the deployment metadata currently available in the repository. `classifications.csv` summarizes each image classification while preserving the ordinal cell-category counts needed to recalculate the Butterfly Index with alternative category values. `temperature_measurements.csv` contains the reviewed camera-overlay temperature extractions. `wind_measurements.csv` contains wind records assigned to the deployment intervals in `deployments.csv`.

`analysis_30_minute.csv` and `analysis_next_day.csv` contain only the identifiers, responses, predictors, adjustment variables, correlation-order variables, and data-coverage fields needed for the two retained manuscript analyses. The next-day table contains the 96 records that passed the manuscript requirement of at least 95 percent overall data completeness.

`data_dictionary.csv` follows the table and field structure used by the example USGS ScienceBase release at <https://www.sciencebase.gov/catalog/item/68d307bad4be025f6ad24e66>. It gives a description, units, and observed minimum and maximum for every released field.

## Time and measurement conventions

All timestamps are local Pacific Standard Time. All currently represented deployments occurred outside daylight-saving time. Temperature values are approximate local camera readings in degrees Celsius. Wind speed and gust values are in meters per second. Wind directions are degrees clockwise from north.

Butterfly Index is an index of visible cluster size. It is not a count of individually identified butterflies. The index assigns the lower-bound values 0, 1, 10, and 100 to the four image-cell categories. Sun-exposed Butterfly Index is the subtotal from occupied cells marked as receiving direct sunlight.

## Known gaps requiring review

The temperature table contains six deployment identifiers that are not yet present in the repository deployment table. They are SC3, SC5, SC11, SLC6_1, UDMH1, and UDMH3. Their metadata should be added from the spatial deployment records when those records become available.

Five images used in the current 30-minute manuscript input are marked unconfirmed in the source classification JSON. Four have nonzero Butterfly Index values and a stored user identifier. The draft release preserves the `classification_confirmed` field and does not alter the manuscript analysis. These records should be reviewed before the release is finalized.

The current tables cover the 2023 to 2024 season. The 2024 to 2025 photographs, classifications, deployment metadata, wind measurements, and any temperature records have not yet been incorporated. The image inventory and photograph archive will be added after those files become available.
