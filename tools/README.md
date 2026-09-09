# Photograph review export

`export_season_photos.py` makes an independent copy of the raw second-season archive, using the `ID` and `deployment_ID` fields in the camera GeoPackage. It never renames or writes to source photographs. JPEG names use the recorded EXIF capture timestamp without filtering dates, correcting clocks, or splitting deployments. Unreadable dates and timestamp collisions retain their original paths under the deployment's `review_needed` folder. Other media retain their paths under `other_media`.

Create an inventory in a new destination, then copy its files. Run from the repository with its Python environment installed. Pillow is included through the existing matplotlib dependency.

```sh
uv run tools/export_season_photos.py plan SOURCE_FOLDER CAMERAS_GPKG NEW_DESTINATION
uv run tools/export_season_photos.py copy NEW_DESTINATION
```

The destination contains a camera metadata snapshot, deployment mapping, SQLite inventory, and CSV manifest. Each copy is checked with SHA-256 before publication. Existing destination files are never overwritten. A repeated copy command resumes unfinished records and accepts an existing file only when its contents match the source. Sources whose size or modification time changed since planning are flagged. `copy --limit 5` can be used for an initial small batch before resuming the complete export.

Leave the export unchanged until copying finishes. Manual changes afterward are not reflected in the original manifest. Source archives and the first-season photo folders remain separate from this review copy.
