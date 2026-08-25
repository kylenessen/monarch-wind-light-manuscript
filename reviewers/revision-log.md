# Revision change log

This working document records substantive decisions and manuscript changes made during the major revision. It is an internal source of truth for preparing the marked manuscript, the point-by-point response letter, and the co-author summary. The formal response letter will be prepared separately.

Work is being completed on the `codex/major-revision` branch. Each entry identifies the source of the request, the decision, the manuscript change, draft response language, verification, and the relevant commit.

## 1. Remove the statistical power analysis

**Status.** Implemented.

**Source.** Reviewer 1, comment 11 in [reviewer-1.md](reviewer-1.md). The reviewer asked how the standardized effect sizes translate into biologically meaningful changes, whether the simulation accounts for important sources of uncertainty, and whether the claim of strong evidence against the hypothesis should be moderated.

**Decision.** Remove the simulation-based power analysis. Its standardized effect sizes could not be translated confidently into biologically meaningful changes in visible cluster size. The simulation also did not represent several important sources of uncertainty or the full structure of the fitted models. Retaining it would add apparent certainty without resolving the reviewer's concern.

**Manuscript change.** Removed the Statistical Power Analysis subsection from the Methods, the corresponding Results subsection and table, and the associated claims about strong evidence against the hypothesis. Replaced the concluding interpretation with a narrower statement that the study failed to detect a consistent wind-disruption effect under the monitored conditions.

**Draft response.** We agree that the simulation-based power analysis did not incorporate uncertainty associated with environmental sensor placement, Butterfly Index classification, image movement or visibility, and limited grove-level replication. In addition, its standardized effect sizes could not be translated confidently into biologically meaningful changes in visible cluster size. We therefore removed the power-analysis Methods subsection, Results subsection and table, and the associated claims about strong evidence against the hypothesis. We now interpret the results as a failure to detect a consistent wind-disruption effect under the monitored conditions.

**Verification.** The manuscript builds successfully. No remaining references to the power analysis, its table, its reported power values, or the removed strong-evidence language were found in the LaTeX source.

**Commit.** `0f0abef` Remove unsupported power analysis.

## Submission deliverables to maintain

The final revision package must include a clean revised manuscript, a version with revisions highlighted, and a point-by-point response letter. The reference list and all DOI links must be audited. Reference 53 requires correction. Any reviewer request that cannot be addressed must receive a direct explanation. The requested extension to 4 September 2026 should be tracked separately until the journal confirms it.
