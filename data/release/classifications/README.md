# Image classifications

The original native JSON files are hosted in the [classifier repository](https://github.com/kylenessen/monarch_trailcam_classifier/tree/main/data/classifications) alongside the software. They are not attachments to the observational release. Matching copies remain in [../../deployments/](../../deployments/) for manuscript analysis reproducibility.

Each deployment JSON contains the native annotations for its photographs. The
deployment identifier in the JSON filename matches deployments.csv. Image keys
match image_filename in photo_index.csv.

The source code and illustrated protocol are available from the
[Monarch Trailcam Classifier](https://github.com/kylenessen/monarch_trailcam_classifier)
and its [classification guide](https://kylenessen.github.io/monarch_trailcam_classifier/).

Files contain an object keyed by image filename, either at the top level or within
a classifications object. Each image record contains cells keyed by cell_row_column.
Each cell stores count, an ordinal category, and directSun, a sunlight flag. Some
older records use sunlight for the same flag. Categories are 0, 1-9, 10-99 and
100-999. Image records also contain confirmed and index, and may contain user,
isNight and notes. These retain confirmation state, image sequence, saved user,
night flag and annotation notes.

The JSON includes unclassified placeholders. classifications.csv summarizes
saved daytime classifications, including unconfirmed annotations and excluding
untouched placeholders. Night records are identified using saved night flags and
recorded SC1 and SC2 night intervals when a JSON flag is absent. Butterfly Index sums category lower bounds of 0, 1, 10 and 100.
Sun-exposed Butterfly Index sums those values for occupied cells marked in sunlight.
