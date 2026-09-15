# ScienceBase upload summary

Measured September 15, 2026 from `/Volumes/MonarchSSD/data_release/publication_package`.

The package contains 226,830 JPEG photographs across 28 deployment folders. The photographs total 332.43 GB. The largest photograph is 3.12 MB. Including all visible supporting files, the package contains 226,853 files totaling 332.64 GB.

| Content | File count | Total size | Largest file |
| --- | ---: | ---: | ---: |
| JPEG photographs | 226,830 | 332.43 GB | 3.12 MB |
| Supporting files | 23 | 203.76 MB | 48.20 MB |
| Complete package | 226,853 | 332.64 GB | 48.20 MB |

Sizes use decimal units. One MB is 1,000,000 bytes and one GB is 1,000,000,000 bytes. The complete package is also 309.79 GiB. These are file content sizes before any archive packaging, rather than allocated disk space.

## Largest files

The largest photograph is `photos/SLC6_3/SLC6_3_20241107123108.JPG`, measuring 3,120,527 bytes. The largest file overall is `classifications/SC1.json`, measuring 48,201,088 bytes. No individual file exceeds 1 GB. The mean JPEG size is 1.47 MB.

## Photographs by deployment

| Deployment | JPEG count | Total GB | Largest JPEG MB |
| --- | ---: | ---: | ---: |
| ARC1 | 8,432 | 15.17 | 3.02 |
| BC01 | 22,289 | 30.53 | 2.81 |
| CR01 | 25,036 | 43.66 | 3.03 |
| MM01 | 25,068 | 33.18 | 2.34 |
| PS01 | 22,923 | 38.59 | 2.48 |
| SC1 | 4,338 | 3.51 | 1.28 |
| SC10 | 3,779 | 3.97 | 1.76 |
| SC11 | 4,449 | 4.62 | 1.63 |
| SC12 | 1,138 | 1.23 | 1.60 |
| SC13 | 15,368 | 22.67 | 2.66 |
| SC2 | 563 | 0.56 | 1.56 |
| SC3 | 3,952 | 3.91 | 1.54 |
| SC4 | 4,751 | 5.37 | 1.76 |
| SC5 | 8,514 | 9.37 | 1.81 |
| SC6 | 3,026 | 2.63 | 1.42 |
| SC7 | 3,035 | 3.25 | 1.70 |
| SC8 | 3,141 | 2.90 | 1.46 |
| SC9 | 3,782 | 4.44 | 1.73 |
| SLC6_1 | 2,455 | 2.66 | 1.63 |
| SLC6_2 | 4,754 | 5.51 | 1.82 |
| SLC6_3 | 4,483 | 8.53 | 3.12 |
| TGR1 | 2,973 | 3.01 | 1.71 |
| TGR2 | 20,889 | 38.25 | 2.86 |
| UDMH05 | 23,303 | 39.97 | 2.67 |
| UDMH1 | 1,895 | 2.14 | 1.69 |
| UDMH2 | 95 | 0.11 | 1.78 |
| UDMH3 | 1,897 | 2.18 | 1.81 |
| UDMH4 | 502 | 0.52 | 1.74 |

## Inventory verification and transfer details

All 226,830 entries in `photo_index.csv` resolve to photographs on disk. No indexed photographs are missing, no additional JPEG photographs were found, and the index contains no duplicate paths. The scan read directory entries and file sizes. It did not validate image contents or checksums.

Twenty-three deployment folders are symbolic links to other locations on the external drive. This inventory follows those links and counts the target files under their publication paths. A transfer or archive must include the target file contents. Copying only the links would leave recipients without those photographs.

Nine hidden `.DS_Store` files were excluded. Raw archives and review copies outside the package were excluded to avoid counting duplicate collections. The 23 supporting files include the existing `data_dictionary_comments.xlsx` review workbook and `photos/SLC6_1/temperature_data.csv`. The count describes the package as currently stored, including these files.

Six deployment collections each exceed 30 GB in total. These are BC01, CR01, MM01, PS01, TGR2, and UDMH05. Their individual photographs remain small. If the transfer team requests archives, archive sizes and file counts will depend on the chosen grouping and compression.

## Suggested email wording

We have now inventoried the proposed release. It contains 226,830 JPEG photographs across 28 deployment folders, totaling 332.43 GB. The largest photograph is 3.12 MB. With the supporting tables, metadata, and other files currently in the package, the total is 226,853 files and 332.64 GB. The largest individual file overall is 48.20 MB.

Could you advise on a bulk transfer workflow, such as a Globus collection or an S3 staging location? Given the number of individual images, would you prefer the deployment folder structure or images bundled into archives? Please let us know any preferred archive size and organization.
