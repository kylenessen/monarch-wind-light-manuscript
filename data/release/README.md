# Monarch monitoring observations, 2023-2025

Kyle Nessen, Peter C. Ibsen, Jay E. Diffendorfer, Francis X. Villablanca.

The reviewed data and metadata contact is Peter C. Ibsen. See [metadata.xml](metadata.xml) for contact details. Cite the [USGS data release](https://doi.org/10.5066/P13IEKEB) by Nessen, Ibsen, Diffendorfer and Villablanca (2026). The citation supplied by Peter gives September 30, 2026 as the publication date.

This release preserves observations from both monitoring seasons at Vandenberg Space Force Base, including deployments outside the manuscript analysis subset. Photographs and available wind measurements cover both seasons. Image classifications and reviewed camera-overlay temperatures cover the first season.

[deployments.csv](deployments.csv) contains 28 rows. One row per camera deployment, including identifiers, WGS84 location, boundaries and known limitations.

[photo_index.csv](photo_index.csv) contains 226,830 rows. One row per retained JPEG photograph. Links images to the deployment table and collection folders.

[classifications.csv](classifications.csv) contains 3,713 rows. One row per saved image classification, with counts of grid-cell categories and Butterfly Index totals. Unclassified placeholders are omitted from this summary.

[temperature_measurements.csv](temperature_measurements.csv) contains 56,066 rows. One row per reviewed camera-overlay temperature measurement.

[wind_measurements.csv](wind_measurements.csv) contains 757,260 rows. One row per wind observation associated with a deployment.

The manuscript repository retains one JSON file per classified deployment in [../deployments/](../deployments/) in the native format of the Monarch Trailcam Classifier. These native JSON files are not release attachments. These files retain cell positions, categories, sunlight labels and saved annotation fields. classifications.csv summarizes saved daytime classifications for use without the software. See classifications/README.md for the JSON structure and software links.

Photographs are stored in photos/deployment_id/ and named deployment_id_YYYYMMDDHHMMSS.JPG using a 24-hour clock. Deployment identifiers may contain underscores. photo_index.csv lists every image path.

Deployment identifiers are unique across both seasons and link all observation tables. Use deployment_id and image_filename together to link image records. Missing observation values are represented by NULL. [data_dictionary.csv](data_dictionary.csv) defines the table fields and photograph collections. N/A marks dictionary units and bounds that do not apply.

Timestamps use device clock times without a UTC offset. The cameras and wind meters do not automatically adjust for daylight saving time. TGR1 photo times were reconstructed as described below. Other timestamps are preserved as recorded.

TGR1 photo metadata and filenames use reconstructed capture times, aligned to the deployment start and end using elapsed time in the numbered image sequence. The camera calendar jump was removed and recording gaps were retained. The visible timestamp overlay still shows the incorrect camera date and time.

Coordinates are approximate camera locations in WGS84, EPSG 4326, expressed in decimal degrees. Locations were recorded with a cellphone under canopy. Some points were adjusted against satellite imagery. Deployment-specific recording information is in deployments.csv.

Wind speed is the average and gust is the maximum speed over each one-minute recording interval, in meters per second. Wind direction is the recorded average in degrees clockwise from north. Wind measurements are provided as recorded within deployment intervals.

Temperature values were extracted from camera overlays using OCR and manually reviewed. The camera readings were not calibrated against a reference thermometer. BI is an index of visible cluster size based on ordinal image-cell categories. Unclassified photographs do not establish butterfly absence.

The [manuscript repository](https://github.com/kylenessen/monarch-wind-light-manuscript) contains the analysis inputs, scripts and results for reproducing the paper. [metadata.xml](metadata.xml) describes this observational release.

The reviewed metadata, dictionary, deployment table and classification summary were synchronized from the canonical publication package on September 16, 2026. The release builder predates these final manual review edits. Regenerating the package requires reapplying them. See the [review record](../../research/data-release-review-2026-09-16.md).
