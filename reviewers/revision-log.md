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

## 2. Remove the simple linear regressions

**Status.** Implemented.

**Source.** The Academic Editor requested a substantially shorter manuscript and a less burdensome statistical presentation. The simple regressions were redundant with the mixed-model analyses and did not account for the repeated-measures or temporal structure of the observations.

**Decision.** Remove the regressions rather than move them to supplementary material. Preserve the analysis code in the repository.

**Manuscript change.** Removed the Linear Regression Results subsection, the combined regression figure, the corresponding Discussion paragraph, and the regression claim in the Conclusions.

**Draft response.** In response to the request to shorten the manuscript and streamline the statistical presentation, we removed the simple linear regressions and their figure. These analyses were redundant with the retained mixed-model analyses and did not account for the repeated-measures and temporal structure addressed by those models.

**Verification.** The manuscript builds successfully. No references to the linear regressions or their figure remain in the LaTeX source.

**Commit.** `f364325` Remove redundant linear regressions.

## 3. Remove the threshold-duration analysis

**Status.** Implemented.

**Source.** Reviewer 1, comments 5 and 10 in [reviewer-1.md](reviewer-1.md). The reviewer noted that a one-minute maximum gust is not equivalent to one full minute of exposure above 2 m/s. The reviewer also identified duplicated candidates in the threshold model set.

**Decision.** Remove the threshold-duration analysis. Its exposure variable counted one-minute sampling intervals containing a maximum gust at or above 2 m/s. It did not measure the actual duration of exposure above 2 m/s. Moving the analysis to supplementary material would not resolve this mismatch.

**Manuscript change.** Removed the threshold-analysis Methods paragraph, Results subsection, candidate-model appendix, and comparisons with the continuous-gust analysis. Revised the objectives, Discussion, and Conclusions so they do not claim an exact test of the historical threshold. Retained descriptive reporting of recorded maximum gusts with an explicit warning that these are not measurements of sustained exposure.

**Draft response.** We agree that our count of one-minute sampling intervals containing a maximum gust at or above 2 m/s did not measure the actual duration of exposure above 2 m/s and was not physically equivalent to the historical threshold formulation. We therefore removed the threshold-duration analysis, its candidate-model appendix, and the associated claims. We retain the observed distribution of maximum gusts as descriptive context and now state explicitly that these measurements do not provide an exact test of sustained exposure above 2 m/s. Because the threshold candidate set is no longer part of the manuscript, its duplicated candidates no longer contribute to any reported model comparison or Akaike weight.

**Verification.** The manuscript builds successfully. No threshold-analysis section, table, appendix, model identifier, or threshold-duration variable remains in the LaTeX source.

**Commit.** `97a2996` Remove unsupported threshold analysis.

## 4. Remove the fixed 24-hour sensitivity analysis

**Status.** Implemented.

**Source.** The Academic Editor requested a much shorter manuscript. The fixed 24-hour analysis repeated the purpose and broad structure of the biologically aligned Next Day Window analysis.

**Decision.** Remove the 24-hour analysis from the manuscript rather than use it as another line of evidence. Preserve its code and generated files in the repository so that it can be restored if an editor requests it.

**Manuscript change.** Removed the 24-hour analysis from the Methods, Results, figures, tables, and candidate-model appendix. Simplified the temporal design to two retained response windows. These are the 30-minute analysis and the Next Day Window analysis.

**Draft response.** To shorten the manuscript and focus it on the two biologically motivated response windows, we removed the ancillary fixed 24-hour sensitivity analysis and its technical appendix. The revised manuscript presents the 30-minute analysis of immediate cluster change and the Next Day Window analysis of delayed cluster change.

**Verification.** The manuscript builds successfully. No reference to the 24-hour analysis remains in the LaTeX source. The underlying code and output files remain available in the repository.

**Commit.** `478db86` Remove 24-hour sensitivity analysis.

## 5. Remove the temporal-window diagram

**Status.** Implemented.

**Source.** The Academic Editor requested fewer figures and suggested removing or relocating technical statistical figures. Reviewer 2 separately requested photographs of the study sites.

**Decision.** Remove the temporal-window diagram. The two retained windows can be described clearly in the Methods. Site photographs will be considered separately as a more useful replacement for the first main-text figure.

**Manuscript change.** Removed the temporal-window figure and caption. No image file was deleted.

**Draft response.** We removed the technical temporal-window diagram and describe the two retained response windows directly in the Methods. This contributes to the shorter statistical presentation requested by the Academic Editor.

**Verification.** The manuscript builds successfully and no reference to the temporal-window figure remains in the LaTeX source.

**Commit.** `40c4e59` Remove temporal window diagram.

## 6. Correct the retained candidate-model comparisons

**Status.** Analysis completed. Manuscript update pending discussion.

**Source.** Reviewer 1, comment 10 in [reviewer-1.md](reviewer-1.md). The reviewer identified duplicate 30-minute candidates and asked how failed Next Day Window fits affected model selection.

**Decision.** Remove exact duplicate candidates M20 and M44 from the 30-minute comparison without renumbering the remaining candidates. Reconstruct the 74 Next Day Window candidates that were defined in the original analysis, then add M79 as a prespecified linear day-scale analogue of the selected 30-minute three-way model. Compare models with different fixed-effect structures using maximum likelihood. Refit each selected model using restricted maximum likelihood for coefficient estimation. Record every attempted formula, fit status, warning, sample size, likelihood method, and information criterion.

**Analysis result.** In the 30-minute analysis, all 50 unique candidates produced rankable fits after the redundant observer random effect was removed. Each deployment was classified by one observer, so observer did not vary within deployment and could not be identified as a separate nested random effect. Removing it left the M16 fixed-effect estimates unchanged and resolved the convergence warning previously recorded for M43. The corrected comparison selected M16, a linear three-way interaction among maximum wind gust, average temperature, and the number of butterflies visible in direct sun, with previous BI as a baseline adjustment. In the Next Day Window analysis, 68 of 75 candidates produced rankable fits and seven produced convergence warnings. The expanded set included M79, a linear day-scale analogue of M16 using mean window temperature and cumulative sun-exposed BI. M79 ranked 24th with $\Delta$AICc = 12.25. M32 remained the selected model with an Akaike weight of 0.613, so the manuscript does not describe its support as decisive.

**Stability audit.** M16 remained the top-ranked candidate when each of the ten deployments was omitted in turn. This included omission of SC10, which contained most of the largest direct-sun observations. M16 also remained first after excluding observations above the 99th percentile and above the 95th percentile of the direct-sun variable. Across every subset, the three-way coefficient remained positive and statistically significant in both the maximum-likelihood comparison fit and the restricted maximum-likelihood coefficient fit. The M16 result therefore does not appear to depend on one deployment or on the largest direct-sun observations.

**Draft response.** We removed the duplicated 30-minute candidates and repeated both retained candidate-model comparisons using maximum likelihood, followed by restricted maximum likelihood refits of the selected models. We also removed observer as a redundant nested random effect from the 30-minute models because each deployment was classified by one observer. All 50 unique 30-minute candidates then produced rankable fits. We reconstructed the Next Day Window set from the formulas actually defined in the original analysis and added a prespecified linear day-scale analogue of the selected 30-minute three-way model. The revised files report all successful and unsuccessful fits and their warnings. The expanded Next Day Window comparison retained M32 as the selected model, with 68 of 75 candidates producing rankable fits. The added three-way M79 candidate ranked 24th with $\Delta$AICc = 12.25. The 30-minute comparison selected M16, and the corresponding manuscript results were revised.

**Verification.** Both scripts completed successfully. The 30-minute audit contains 50 unique formulas. The Next Day Window audit contains 75 unique formulas. No duplicated formulas remain in either retained candidate set.

**Commit.** `f2468ce` Correct retained model comparisons.

## Submission deliverables to maintain

The final revision package must include a clean revised manuscript, a version with revisions highlighted, and a point-by-point response letter. The reference list and all DOI links must be audited. Reference 53 requires correction. Any reviewer request that cannot be addressed must receive a direct explanation. The journal granted the requested extension. The revised deadline is 4 September 2026.
