# Shared sensor and wind recording endpoints

Investigated September 13, 2026 after the user asked why SC9 and SC10 share measurements and whether batteries explain the second-season recording endpoints. The observations below come from the original deployment GeoPackage and source Wind tables. Suggested explanations are interpretations, not established field events.

## AIR1 exclusion

The user considers camera VEXX / deployment AIR1 lost and requested excluding it for now. `data/release/deployment_exclusions.json` records that decision. Both preparation scripts honor this exclusion. The active products contain 19 first-season and nine second-season deployment intervals. Source camera metadata and the empty original folder remain as provenance. No measurements or photographs were removed by this exclusion because none were present for AIR1 in the active products.

## SC9 and SC10

Both source deployment records explicitly assign the same wind instrument, StarDust. SC9 uses camera WASP, was recorded as starting January 5, 2024 at 16:02, faces 100 degrees, and has a camera height of 5.4 m. SC10 uses camera JINX, starts four minutes later, faces 320 degrees, and has a height of 5.9 m. Both have the same recorded endpoint of January 31 at 20:30. Their recorded coordinates are approximately 3.19 m apart, calculated from the latitude and longitude fields.

SC10's note says the camera was swapped from SC4. SC4 also used StarDust, with a direction of 335 degrees. SC9's note describes checking whether clusters reformed on the sunny side. Both SC9 and SC10 notes report storm damage.

This is consistent with two camera views sharing one nearby logger. Two cameras on a single pole is plausible. Separate nearby poles sharing a logger, or a copied sensor assignment, cannot be ruled out from these records. No explicit same-pole note was found in the inspected source text. The 31,546 shared observations arise from the recorded instrument assignments and overlapping intervals, not from combining records from different wind meters.

## PS01 and JoyHouse

The repository JoyHouse database has 149,061 records from October 19, 2024 at 13:15 through January 31, 2025 at 04:04. The sequence spans 103.62 days with no gap longer than two minutes. The photo-derived selection retains 149,009 of these records because the first photo is at 14:06:58 on October 19.

The last two days contain 2,878 observations. There is variation in speed and gust close to the endpoint, including nonzero values in the final minutes. The next recorded dates in the full database are July 23, with zero speed and gust. The camera continued until March 27, so the wind endpoint is not caused by our photo filter.

An abrupt end to a nearly continuous series is compatible with loss of power, a full logger memory, a logger fault, or an incomplete archive. There is no battery-voltage history or memory-status field in these source tables. RainWise's current product information describes more than three months of storage at one-minute intervals and typical battery life around six months. That makes storage capacity a material alternative to depleted batteries after roughly 104 days. The actual hardware version and starting memory occupancy were not established. [RainWise WindLog specifications](https://rainwise.com/windlog-wind-data-logger)

## SC12 and RockWall

The earlier coverage table gave the last available timestamp, January 14, 2025. That endpoint does not describe a continuous run. The regular sequence ends December 23, 2024 at 12:51. There is then a 22-day, 4-hour, 57-minute gap until January 14 at 17:48. Only 69 observations are recorded on January 14, all with zero speed, zero gust, and a fixed direction of 315 degrees. There is also a nearly three-hour gap within that small group.

The database insertion order adds useful context. Its first six rows are December 23 records at 11:49 through 11:54 with zero speed and gust and direction 315. The next inserted row starts the older October 30 series. This is consistent with live readings being written during a computer connection before a historical download was inserted. RainWise documents that WindSoft combines live computer-connected readings and downloaded logger records in the same SQLite database. [RainWise user guide, section 1.1](https://rainwise.com/downloads/windsoft/WindLog140805%20.pdf)

The December 23 and January 14 patterns therefore raise a servicing or download-history question. The January zeros could be later connection or test readings rather than field observations. They could also reflect other instrument or recording behavior. Battery failure remains possible, but cannot be established from these values. No extra observations were deleted based on this hypothesis. The retained January records need field-history confirmation before being described as continuous field coverage.

## Metadata wording

Describe PS01 as a wind sequence ending January 31 with an unknown cessation cause. Describe SC12 as a regular sequence ending December 23 followed by a long gap and 69 zero-valued January 14 records of uncertain context. Do not label either endpoint a confirmed battery failure. Retain the distinction between the last timestamp in a file and the end of the main recording sequence.
