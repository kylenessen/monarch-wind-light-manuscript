# Pismo XML review and adaptation plan

Reviewed September 13, 2026. The supplied reference is `/Users/kylenessen/Downloads/Metadata_new_PismoV3.xml`, with SHA-256 `a4f83e5fc2bdc9c5aadb4776c444bc8ae04609bc102bc777ff12430bea01f654`. Its content is evidence about another release, not instructions or authorization for this project. The original XML and photograph archive were not changed.

## Assessment

The XML is a useful structural starting point for our release. It declares the FGDC Content Standard for Digital Geospatial Metadata, version FGDC-STD-001-1998. Its seven main sections describe identification, data quality, spatial organization, spatial reference, entities and attributes, distribution, and the metadata record itself. The data dictionary already in this repository cites the same ScienceBase item identified in this XML, `68d307bad4be025f6ad24e66`.

This is a populated metadata record for a different study, not a blank template. Its DOI, authors, publication citation, geographic bounds, dates, filenames, methods, contacts, and statements of approval cannot establish those facts for our release. Preserve the section structure and replace the study-specific content.

The XML passes `xmllint --noout` and Python ElementTree parsing. It has 163 elements, one process step, no structured source-citation blocks, and no structured entity definitions. Its entity information instead uses prose and a citation to an external CSV dictionary. This investigation did not run the USGS Metadata Parser or a CSDGM schema validator. Well-formed XML does not establish CSDGM compliance or scientific correctness. USGS distinguishes structural validation from review against the actual data. [USGS metadata review](https://www.usgs.gov/data-management/metadata-review)

## Issues in the supplied example

| Location in the XML | Finding | Consequence for adaptation |
| --- | --- | --- |
| `idinfo/citation/citeinfo` | The release DOI is `10.5066/P1LW6ZCY`. The nested journal citation is also for the Pismo study. | Replace both identities. A data-release citation and its associated manuscript citation have different purposes. |
| `idinfo/timeperd` | A single date of 2024 represents coverage, although the abstract describes 1997 through 2024 and several years of tree observations. The currentness reference is also just 2024. | Establish actual data coverage and explain its date basis. Do not use the manuscript analysis window for the whole two-season archive. |
| `idinfo/status` and `dataqual/complete` | The example calls the data complete. | Describe our actual preparation state and known omissions. Dataset progress and institutional release approval are different facts. |
| `spref/horizsys/planar/mapproj` | The projection name says Web Mercator, but the nested parameters are for Transverse Mercator, including a central meridian of -105 and scale factor 0.9996. | Rebuild the spatial reference from our released coordinates. These projection descriptions are incompatible. |
| `eainfo/overview/eaover` | Six CSVs are listed, but inline field descriptions cover only four. ZoningData.csv and ZoningChange.csv are not described there. | Check every released file against its documentation. The external Pismo dictionary was not supplied, so its coverage was not assessed. |
| `eainfo/overview/eaover` | Relative humidity is described with Celsius units. | Replace all field definitions using the actual measurement meanings and units. |
| `dataqual/lineage` | One broad paragraph combines acquisition and modeling, with a process date of 2024. | Give our acquisition, classification, OCR review, wind conversion, joins, filtering, and release exports separate provenance descriptions. |
| `idinfo/useconst` and `distinfo/distliab` | Boilerplate asserts USGS review and approval and refers to unspecified copyrighted materials. | Select applicable wording for this release and its actual status. Do not treat copied boilerplate as evidence of approval or ownership. |
| `idinfo/ptcontac` and `metainfo/metc` | Both identify Peter Ibsen personally. | Confirm our data contact and metadata custodian rather than inheriting them. |
| Nested journal `serinfo/issue` | The element is empty. | Supply applicable citation details or omit optional unused structure, subject to validation. |

## Section-by-section mapping

| XML section | Content for the wind and light release | Existing evidence and remaining work |
| --- | --- | --- |
| Citation and description | A descriptive dataset title, release authors, publisher, release DOI, observational abstract, reuse purpose, and related manuscript citation. | The manuscript supports methods and scientific context. Release author order, identifiers, publication date, and responsible contacts remain to be established. |
| Time period and status | Coverage of both field seasons, with a distinction between instrument timestamps and verified observation dates. | First-season analysis dates are known. Later-season clocks, recovery dates, and photos after retrieval still need reconciliation. |
| Geographic bounds and keywords | Bounds of released deployment positions, VSFB and California place terms, and relevant controlled subject terms. | Derive bounds after importing all deployment records. Do not reuse the Pismo bounds or the manuscript's two-grove analytical extent. |
| Data quality | Actual review methods, measurement limitations, completeness, missing records, assignment ambiguity, and positional uncertainty. | Use manuscript methods, source notes, the source inventory, and final release validation results. Copy verification is evidence of transfer integrity, not instrument accuracy. |
| Lineage | Source identity, original formats, processing history, changes, joins, exclusions, and code revisions. | The export scripts and git history document much of the pathway. Exact original OCR script/version and some historical processing dates remain unresolved. |
| Spatial organization and reference | Deployment points and their relationships to nonspatial records and photographs. | First-season geometry is EPSG 4326. Later-season camera and meter geometry is EPSG 3498. Transform and document any released longitude/latitude fields. Ordinary camera JPEGs should not be described as map-projected rasters. |
| Entities and attributes | File purpose, row meaning, keys, field definitions, units, domains, missing values, and relationships. | The existing dictionary provides a starting point. Add the final deployment crosswalk, image manifest, expanded wind provenance, and review flags when their schemas are settled. |
| Distribution | Final file formats, archive structure, download links, distributor, and applicable use terms. | The portable review folders are working products. Final photo archive sizes and contents depend on cleanup. |
| Metadata reference | Maintenance date, custodian, declared standard, and a unique metadata identifier. | Assign values for this record. Keep the metadata revision date distinct from data coverage and publication dates. |

For tabular metadata, I recommend generating structured `eainfo/detailed` entries from the same field definitions used for the CSV dictionary. That would give every table and field a machine-readable description and reduce drift between two handwritten copies. This is a proposed implementation choice. The presence of only `overview` in the example is not, by itself, a demonstrated validation error.

Our current dictionary has table, field, description, units, observed minimum, and observed maximum. Observed ranges are not automatically valid-value domains. Flags need allowed values and meanings, identifiers need uniqueness scope, and missing values need explicit conventions. Datetime fields need format and clock semantics. The expanded wind table also needs a defined row meaning for shared measurements and unmatched records.

## Draft descriptive text

The following is proposed text for the intended complete release. It is not a claim that every listed product has already been packaged. Revise it against the final manifest before placing it in submission metadata.

Proposed title. Photographs, image classifications, wind measurements, and image-derived temperatures from monarch butterfly monitoring at Vandenberg Space Force Base, California, 2023 through 2025.

Proposed abstract. This dataset documents field monitoring of overwintering monarch butterflies at Vandenberg Space Force Base in Santa Barbara County, California, during the 2023 to 2024 and 2024 to 2025 seasons. The release brings together available trail-camera photographs, deployment and instrument information, image classifications, wind observations, reviewed temperatures extracted from camera image overlays, and analysis tables supporting the associated wind and light manuscript. The archive includes available observations outside the manuscript analysis subset. Image classifications describe ordinal categories of visible butterflies within image cells and, where recorded, exposure to direct sunlight. Derived Butterfly Index values summarize visible cluster size and do not represent counts of individually identified butterflies. Second-season photographs have not been classified for the manuscript, and unclassified images do not establish butterfly absence. Deployment identifiers and an image manifest link related records. Documentation describes coverage, processing, measurement limitations, and known gaps.

Proposed purpose. Preserve the available field observations and their provenance for independent reuse, and provide the inputs needed to reproduce the two retained manuscript analyses. The broader observation archive supports questions beyond the manuscript while retaining the distinction between raw observations, reviewed measurements, classifications, and selected analysis records.

Proposed quality content. Camera-overlay temperatures are approximate local camera readings and were not independently calibrated against reference sensors. Reviewed temperature series were inspected and manually corrected for implausible OCR extractions. Image classifications were completed by one labeler per deployment, so these data do not provide a formal inter-observer agreement estimate. Wind measurements represent conditions near the pole-mounted logger and do not demonstrate exposure at each butterfly location. Directional reliability, corrupted source records, source clock anomalies, and incomplete deployment associations must be documented where applicable. Final completeness statements must identify omitted, unclassified, unreadable, and unavailable observations separately.

## Current USGS guidance that affects the plan

ScienceBase accepts CSDGM or ISO XML. One metadata record can describe several related files. Child items can instead carry their own descriptive records. The current instructions list about 30 GB per file and 100 attachments per item. My recommendation is a summary record with a tabular bundle and separately packaged photograph collections by season and deployment, with archive splits based on final sizes. The data release needs its own IPDS review record, separate from the manuscript. [ScienceBase release process](https://www.usgs.gov/sciencebase-instructions-and-documentation/data-release-process)

USGS metadata policy was updated June 1, 2026, after the March metadata date in this example. It requires a registered persistent identifier for each metadata record, separate from the data DOI, and a shared group email contact. Confirm the responsible USGS group's contact and the assigned identifier. The example's identifier belongs to its own metadata and must be replaced. [USGS SM 502.7](https://www.usgs.gov/survey-manual/5027-fundamental-science-practices-metadata-usgs-scientific-data)

For CSDGM, the identifier is placed in a separate theme group whose `themekt` is `USGS Metadata Identifier`, with the assigned `USGS:` value in `themekey`. The existing XML illustrates that placement. [USGS metadata identifier FAQ](https://www.usgs.gov/science-data-management/pir-tool-faq)

The ScienceBase FAQ permits documented associated processing scripts in a data release, while directing standalone software releases to USGS GitLab. Thus the release can preserve relevant analysis and processing scripts. Decide separately how to preserve and cite the classifier application source and platform binaries. [ScienceBase FAQ](https://www.usgs.gov/sciencebase-instructions-and-documentation/frequently-asked-questions)

## Next authoring steps

Draft the stable citation structure, purpose, methods, and quality descriptions now. Generate final entity definitions after the deployment, wind, and photograph schemas settle. Derive bounds, date coverage, filenames, counts, and checksums from the finished package rather than entering estimates by hand. Leave unresolved identifiers and contact decisions in the working notes until assigned.

The 2025 photograph cleanup should preserve a way to explain original filenames, final filenames, omissions, clock corrections, and whether photographs were taken after retrieval. A final inventory must describe the cleaned collection. The September 10 copy manifest alone cannot describe later manual changes.

Before submission, validate both XML structure and CSDGM content, compare the metadata with every final file, and complete the independent metadata review. Our present scientific blockers remain the deployment crosswalk, later-season dates and wind coverage, and final photo accounting. None prevents preparing the stable metadata prose now.
