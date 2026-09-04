# Coauthor edit reconciliation, 4 September 2026

The September 3 email from Francis Villablanca says that he made clarification edits in both the revised manuscript and the tracked version and approved resubmission. The files in the shared OneDrive Manuscript folder contain edits that were absent from the LaTeX source at commit `497d974`. The two shared Word files do not contain the same edits. This reconciliation combines their changes without replacing newer repository corrections with older Word content.

The email reports Francis's approval. It does not independently document approval from every coauthor. Word records the recent tracked editor as Guest User, so individual changes cannot be conclusively attributed to a named author from document metadata.

## Sources and preservation

The source folder is `/Users/kylenessen/Library/CloudStorage/OneDrive-CalPoly/Manuscript`. The clean manuscript was last modified internally on September 3 at 17:00 UTC. The tracked manuscript contains seven insertion and deletion records attributed to Guest User on September 2 at 13:36 to 13:39 UTC. These records represent two statistical wording edits. Other shared-file changes were made directly in existing text and are detectable by comparing the files, even though they have no separate recent revision record.

The SHA-256 of the shared clean manuscript is `8ca213ee119877049c104529f2eecaed637225fe11eb3488633b7345729ad57c`. The SHA-256 of the shared tracked manuscript is `53691829969e9e2140e9ce3b06cc951110573e970e950ad2b068048d8be4293c`. The SHA-256 of the shared response letter is `238a1bc4d2ad9edb13215ba339fa7fabdac38989b2725663c007dac9495d0e07`.

Read-only source snapshots, extracted accepted text, raw revision records, paragraph differences, and the pre-edit LaTeX are preserved locally in `exports/coauthor-audit-20260904/`. The shared folder was not modified. The pre-existing local Word changes and editor annotations were not overwritten or committed.

## Applied edits

Thirteen edits were missing from LaTeX across ten paragraphs. This table records the complete reconciliation. Clean means the shared revised-submission Word file. Tracked means the accepted-text reading of the shared revision-tracked Word file.

| Location | Source | Applied change |
| --- | --- | --- |
| Introduction, paragraph 1 | Clean only | Clarify recurrence in the same grove areas and trees. |
| Introduction, paragraph 2 | Clean only | Specify overwintering studies in central California. |
| Introduction, paragraph 2 | Clean only | Specify trees and grove locations associated with aggregations. |
| Introduction, paragraph 2 | Clean only | Specify that the historical wind speeds were in groves. |
| Introduction, paragraph 3 | Both | Clarify that winds were treated as disruptive, not necessarily just at clusters. |
| Monitoring methods, wind direction paragraph | Both | Add the relationship between nearby wind measurements and the historical hypothesis. Normalize Disruptive Wind Hypothesis to the manuscript's defined Wind Disruption Hypothesis. Retain the measurement limitations. |
| Next Day statistical methods | Tracked only | Replace separate candidates with separate statistical models. |
| Model comparison methods | Tracked only | Introduce multiple candidate generalized additive mixed models. Correct the source phrase multiple “candidates” generalized additive mixed models. |
| Discussion, previous microclimate work | Both | Add Saniee and Villablanca 2022 to the light-related habitat citations. |
| Discussion, previous microclimate work | Both | Acknowledge that earlier physiological research had already been proposed as a mechanistic alternative. Restore citations to Masters 1988, Kammer 1970, Barker and Herman 1976, Chaplin and Wells 1982, and Saniee and Villablanca 2022. |
| Discussion, physiological explanation | Both | Begin with Monarch butterfly physiology offers one possible explanation. |
| Discussion, proposed framework | Both | Add latitudinally variable to interacting environmental conditions. |
| Discussion, inference limits | Both | Specify one military installation. |

The numbered Word citations were mapped to existing BibTeX keys. No new bibliography entry or analytical result was introduced. The scientific claims in the edits were transferred as coauthor revisions, not independently reviewed as a new literature search.

## Differences deliberately retained

Seven reference URLs in the shared clean manuscript predate the repository's September 2 bibliography correction at `a393764`. The corrected repository URLs were retained. The LaTeX references target Appendix B.1 and B.2. The old Word exporter collapsed these to Appendix B. That export defect was corrected while preparing the fresh Word copy. The original submission Word file is byte-identical between the shared folder and repository. The response letter has identical accepted paragraph text, despite package and metadata differences. No comments were found in the two shared manuscript files or the response letter.

The existing local revised Word file also has uncommitted formatting and mathematical-character changes. It was preserved as found. Fresh submission artifacts are written separately so that those local changes and the shared review evidence remain intact.

## Export corrections discovered during verification

Visual review of the fresh Word export exposed existing converter defects. The converter dropped the min and max operators from temperature subscripts in the candidate tables, numbered appendix subsections as 5.1 and 5.2, and omitted A from appendix table references. The converter now preserves T_min and T_max, uses B.1 and B.2, and matches references to the displayed table numbers A1 through A5. These fixes affect export fidelity, not the LaTeX analysis or coauthor wording.

## Verification and prepared files

The clean LaTeX manuscript builds to 18 pages with no unresolved citations or references and no overfull boxes. All 13 replacement strings were checked against the committed manuscript. The fresh Word export renders to 18 pages. Every page was inspected, and the affected pages were inspected again after correcting the exporter. All 27 temperature-specific Next Day candidate rows preserve their expected min, max, or previous-temperature symbols. Appendix headings, subsection references, and table references were checked against the source.

The clean PDF, body-text comparison PDF, response letter, and cover letter were rendered and visually inspected. The 18-file LaTeX source archive was extracted to a separate directory and successfully rebuilt. The statistical review folder was packaged without changing its data, scripts, or results. ZIP integrity checks passed.

Prepared files are in `exports/resubmission-2026-09-04/`, with a README explaining the file roles and the comparison format. `SHA256SUMS.txt` records the deliverable checksums. The 35-page comparison retains deleted body text against submission commit `12b7cc9`. It presents front matter and table interiors in their current form, and references to removed figures and tables retain historical numbers. Final numbering is authoritative in the clean manuscript.

The coauthor changes are committed at `611a34e`. Word conversion fixes and the refreshed cover date are committed at `47defad`. The shared OneDrive files and the two pre-existing local modifications remain untouched. No journal submission, email, data release, or DOI publication was performed.
