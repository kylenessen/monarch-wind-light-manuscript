# Image classifications

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
confirmed records and saved annotations, excluding untouched placeholders. Its
is_night field also uses recorded night intervals for SC1 and SC2 when a JSON flag
is absent. Butterfly Index sums category lower bounds of 0, 1, 10 and 100.
Sun-exposed Butterfly Index sums those values for occupied cells marked in sunlight.
