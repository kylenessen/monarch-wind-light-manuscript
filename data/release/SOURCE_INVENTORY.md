# QGIS deployment source investigation

Inspected September 9, 2026. Sources were read without modifying the `masters` repository. The source directory is `/Users/kylenessen/GitHub/masters/VSFB_Monarchs`.

The active project is `VSFB_Monarchs.qgs`. Its `deployments`, `cameras`, and `wind_meters` layers reference `deployments.gpkg`, `cameras.gpkg`, and `wind_meters.gpkg` in that directory. The project and camera GeoPackage have uncommitted changes. Findings describe those working files, including the current camera deployment IDs.

## First-season deployments

`deployments.gpkg` contains 19 records covering the 2023 to 2024 season. It includes all 12 deployments in the manuscript repository and seven additional IDs. These are SC3, SC5, SC11, SLC6_1, TGR1, UDMH1, and UDMH3. This locates the metadata for all six temperature deployment IDs previously identified as missing.

The layer includes deployment and recovery timestamps, camera and wind meter names, camera height, viewing distance and direction, cluster count, photo interval, monarch presence, status, notes, video links, latitude, and longitude. Its geometry uses EPSG 4326. Additional release fields should retain the field notes and documented measurement meanings.

Using these intervals with the 11 wind databases already in the manuscript repository matches 500,405 distinct source rows, compared with 278,796 using the current manuscript deployment table. That adds 221,609 assigned records. Another 180,608 source rows remain outside these first-season intervals. This comparison uses the existing exporter's inclusive interval boundaries truncated to whole seconds. It does not establish measurement validity or assign later-season records.

SC3 has `NA` as its wind meter name. UDMH1 has a note that its SunRuler wind data are corrupted. TGR1 has a note that the image dates were not set. SLC6_1 notes that photographs taken after the camera fell were deleted. Preserve these limitations when describing completeness and data quality.

SC9 and SC10 still reference the same sensor during overlapping intervals. SC10 spells the sensor `Stardust`, while SC9 and the database filename use `StarDust`. The comparison above used case-insensitive sensor matching. The shared sensor relationship still needs interpretation before choosing the final wind CSV row structure.

`pole_locations.gpkg` is an older, less complete source with 16 records, several unfinished recovery fields, and differing times. Prefer the active `deployments` layer as the candidate first-season source while retaining provenance for any discrepancies.

## Later-season cameras and wind meters

`cameras.gpkg` contains 10 records. Its `deployment_ID` field gives the following mapping. These are the current source identifiers, pending resolution of the repeated SC12 ID.

| Deployment ID | Camera ID | Wind meter ID | Camera record creation date |
| --- | --- | --- | --- |
| MM01 | NOVA | LeafWind | 2024-10-19 |
| PS01 | EM03 | JoyHouse | 2024-10-19 |
| CR01 | GOLD | VineLoop | 2024-10-19 |
| SC12 | IRIS | RockWall | 2024-10-31 |
| UDMH05 | JADE | LeftLion | 2024-10-31 |
| SLC6_3 | KIWI | BarkRoar | 2024-11-07 |
| BC01 | APEX | EchoBuzz | 2024-11-07 |
| TGR2 | MOSS | CatFable | 2024-11-17 |
| AIR1 | VEXX | FireSong | 2024-11-17 |
| ARC1 | ORCA | BoltZoom | 2024-11-17 |

The user identifies these as the later season that includes 2025. The layer itself records creation timestamps in October and November 2024, with a literal `Z` suffix. It has no explicit deployment-start or recovery fields. Creation timestamps must not automatically become measurement interval boundaries or be interpreted as local PST. Confirm timestamp semantics and obtain recovery dates from field records or archive evidence.

The camera layer also contains notes, viewing direction, viewing distance, camera height, and geometry. The companion `wind_meters.gpkg` has 10 records with sensor ID, notes, creation timestamp, height, and geometry. Every camera's `wind_meter_ID` matches a wind meter `ID`. Preserve the separate camera and wind sensor positions and heights.

Both later-season geometries use EPSG 3498, named NAD83(NSRS2007) / California zone 5 (ftUS). Transform geometry before publishing longitude and latitude. The projected geometry units do not establish the units of manually entered height and distance attributes.

SC12 is already used in the first-season deployment layer for NOVA with BlueLake in January to February 2024. The later camera record uses SC12 for IRIS with RockWall. Coordinate a unique release identifier with the photograph task and retain the original IDs in a crosswalk. Do not rename source layers or image files as part of this investigation.

The QField download copy of `cameras.gpkg` contains 10 rows but lacks `deployment_ID`. The backup copy contains zero rows and also lacks that field. Use the current main camera layer as the candidate mapping source, rather than those copies.

No databases named for the nine other later-season sensors were found in the inspected `masters` repository. Its six `.s3db` files under `memos/data/sensors` have different sensor names. JoyHouse is present in the manuscript repository and has records extending into 2025, but its PS01 interval still needs to be established. The remaining later-season wind archive location is unresolved.

## Source fingerprints

These SHA-256 values identify the working files inspected. They are provenance notes, not frozen source copies.

| File | SHA-256 |
| --- | --- |
| `VSFB_Monarchs.qgs` | `72555379fcbae85504388bf010ec3afbb78328f40c973a4eee73266cf8413c9e` |
| `deployments.gpkg` | `37dc7cb3d9e57a2cb92cd1d83fcb31d745f035879a31b9a16e9d9b6423a211f8` |
| `cameras.gpkg` | `21f0751bbc1e10393a244ff8f749a130dfbbcdfce6100ca8f22285adb2055a65` |
| `wind_meters.gpkg` | `976b923f0595f14f1936d5f2a50f678d3f6032251ae138a2efdefd8c94c7283b` |

The next preparation step is a reproducible import of both deployment sources with source identifiers and season information. Preserve camera and sensor metadata, add a documented identifier crosswalk, and flag unavailable intervals. Resolve recovery dates and locate the remaining wind archives before treating later-season wind assignments as complete.
