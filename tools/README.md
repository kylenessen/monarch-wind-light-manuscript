# Archive preparation utilities

These scripts supported preparation and transfer of the observational release. They are separate from the [manuscript reproduction workflow](../analysis/README.md). Drive paths in the historical examples below refer to the original preparation environment. The [operations records](../research/operations/README.md) describe subsequent recovery and delivery.

# Photograph review export

`export_season_photos.py` makes an independent copy of the raw second-season archive, using the `ID` and `deployment_ID` fields in the camera GeoPackage. It never renames or writes to source photographs. JPEG names use the recorded EXIF capture timestamp without filtering dates, correcting clocks, or splitting deployments. Unreadable dates and timestamp collisions retain their original paths under the deployment's `review_needed` folder. Other media retain their paths under `other_media`.

Use one command to inventory, copy, and verify the entire archive. The script declares its own Pillow dependency for `uv`, so it can also run as a standalone file copied onto the portable drive. Rerun the same command to resume an interrupted inventory or transfer.

```sh
uv run tools/export_season_photos.py run SOURCE_FOLDER CAMERAS_GPKG NEW_DESTINATION --background
```

`--background` detaches the job from the terminal or assistant session. On macOS it prevents idle system sleep while running. The job writes `NEW_DESTINATION.log` and `NEW_DESTINATION.status.json` alongside the export folder. The status becomes `completed`, `interrupted`, or `failed`, with details when something needs attention. No supervision or intermediate commands are required. Omit `--background` to run in the foreground.

When the source and destination share an APFS volume, the script uses independent copy-on-write clones. These initially share disk blocks, but editing or deleting a copy does not change the original. This avoids requiring enough free space for a second physical copy of the entire archive. A small independence probe checks clone support before choosing this method. On other filesystems the script makes ordinary copies and checks that sufficient space is available. It never falls back silently from clones to a full-size transfer.

The destination contains a camera metadata snapshot, deployment mapping, SQLite inventory, and CSV manifest. Each copy is checked with SHA-256 before publication. Existing destination files are never overwritten. A repeated command resumes unfinished records and accepts an existing file only when its contents match the source. Sources whose size or modification time changed since planning are flagged. A process lock prevents two unattended runs from writing to the same export concurrently. Existing completed copies are left alone on resumption.

For this portable drive, use the standalone script and camera snapshot in `/Volumes/MonarchSSD/data_release`.

```sh
cd /Volumes/MonarchSSD/data_release
uv run export_season_photos.py run 'raw/VSFB 2025' cameras.gpkg VSFB_2025_Deployment_Review --background
```

The separate `plan` and `copy` commands remain available for existing exports. Run the regression checks from the repository with `uv run --no-sync python -m unittest discover -s tools -p 'test_export_season_photos.py'`.

Leave the export unchanged until copying finishes. Manual changes afterward are not reflected in the original manifest. Source archives and the first-season photo folders remain separate from this review copy.

## Recording durations

`camera_recording_duration.py` reads the saved inventory and camera snapshot without opening or changing photos. It reports the longest timestamp segment for each camera, splitting at gaps greater than 24 hours by default. All other segments remain documented, so stray old clock dates do not inflate the main duration. The report includes exact endpoints, elapsed days, photo counts, typical intervals, gaps, duplicate timestamps, and empty cameras. These observed spans do not establish battery life or explain why recording ended. Videos do not contribute to the photo timestamp spans.

```sh
uv run tools/camera_recording_duration.py /Volumes/MonarchSSD/data_release/VSFB_2025_Deployment_Review --output /Volumes/MonarchSSD/data_release/VSFB_2025_duration_report
```

The command writes Markdown and JSON reports. Use `--gap-hours` to adjust the segment boundary. Reports use the export inventory as recorded during copying, so later manual changes to images are not included. Run the duration checks with `uv run --no-sync python -m unittest discover -s tools -p 'test_camera_recording_duration.py'`.
