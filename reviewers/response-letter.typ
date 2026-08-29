#set document(title: "Response to the Academic Editor and Reviewers")
#set page(paper: "us-letter", margin: (top: 0.78in, bottom: 0.78in, x: 0.82in))
#set text(font: "Libertinus Serif", size: 10.5pt, lang: "en")
#set par(leading: 0.62em, justify: true)
#set heading(numbering: "1.", outlined: true)
#set page(numbering: "1")

#let comment(body) = block(
  fill: rgb("f2f5f7"),
  inset: 10pt,
  radius: 3pt,
  above: 0.7em,
  below: 0.55em,
  [#text(weight: "bold")[Reviewer comment] #body],
)

#let response(body) = block(
  breakable: false,
  stroke: (left: 1.2pt + rgb("2f6f70")),
  inset: (left: 10pt, right: 2pt, top: 1pt, bottom: 1pt),
  above: 0.25em,
  below: 0.7em,
  [#text(weight: "bold", fill: rgb("1d5051"))[Response] #body],
)

#let locations(original, revised: [Pending final line-numbered revised PDF]) = table(
  columns: (1.55in, 1fr),
  stroke: none,
  inset: (x: 3pt, y: 2pt),
  align: left + top,
  [#emph[Original anchor]], [#original],
  [#emph[Revised location]], [#revised],
)

#align(center)[
  #text(size: 17pt, weight: "bold")[Point-by-Point Response]
  #v(0.35em)
  #text(size: 13pt)[Response to the Academic Editor and Reviewers]
  #v(1.2em)
  *Manuscript title:* _Wind Does Not Disrupt Overwintering Monarch Butterfly Clusters: Direct Empirical Test of a Three-Decade Management Assumption_
  #v(0.35em)
  *Journal:* Insects
  #v(0.35em)
  *Revision:* Major revision
]

#v(1.7em)

Dear Academic Editor and Reviewers,

We thank you for the careful and constructive evaluation of our manuscript. We have revised the manuscript to address the concerns about the scope of inference, environmental measurements, analysis, interpretation, length, and reproducibility. This document responds to each comment in the order received. Reviewer wording is reproduced verbatim in shaded blocks. Each response identifies the revision made or the work that remains to be completed before resubmission.

The original line references below are preserved exactly as supplied in the reviews. Once the revised manuscript is final, we will compile a line-numbered revised PDF and replace each pending location with its final page and line reference. We will not use source-file line numbers as a substitute for those PDF anchors.

#heading[Revision map]

The journal-facing response remains point by point. The following internal map links the response sections to the working issues that organize implementation by theme.

#table(
  columns: (1.25in, 1.75in, 1fr),
  fill: (x, y) => if y == 0 { rgb("e6eeee") } else { none },
  inset: 5pt,
  align: left + top,
  [*Source*], [*Comments*], [*Working theme*],
  [Academic Editor], [Overall, points 1 and 2], [#link("https://github.com/kylenessen/monarch-wind-light-manuscript/issues/34")[Scope] and #link("https://github.com/kylenessen/monarch-wind-light-manuscript/issues/41")[compression]],
  [Reviewer 1], [1, 3, 13], [#link("https://github.com/kylenessen/monarch-wind-light-manuscript/issues/34")[Scope and management]],
  [Reviewer 1 and 2], [R1 4 to 7, R2 3], [#link("https://github.com/kylenessen/monarch-wind-light-manuscript/issues/35")[Environmental measurements]],
  [Reviewer 1], [8 and 9], [#link("https://github.com/kylenessen/monarch-wind-light-manuscript/issues/36")[Butterfly Index and replication]],
  [Reviewer 1], [10 and 11], [#link("https://github.com/kylenessen/monarch-wind-light-manuscript/issues/37")[Model audit and inference]],
  [Reviewer 1], [12 and 13], [#link("https://github.com/kylenessen/monarch-wind-light-manuscript/issues/38")[Direct observations and mechanisms]],
  [Reviewer 1], [14], [#link("https://github.com/kylenessen/monarch-wind-light-manuscript/issues/39")[Reproducibility]],
  [Reviewer 1], [2 and minor comment 1], [#link("https://github.com/kylenessen/monarch-wind-light-manuscript/issues/40")[Historical framing]],
)

#heading[Academic Editor]

#heading(level: 2)[Overall assessment]

#comment[
The manuscript has been reviewed by two peer-reviewers, and both feel that the manuscript has merit, and it addresses a topic of conservation concern, though both reviewers noted similar problems with the methodology, and with the interpretation of results. Specifically, both reviewers pointed out (rightly so) that the entire project hinges on observations of just two localities, and from only one field season. Moreover, both reviewers point out that the findings from this limited study appear to be overly exaggerated, or at least, are not as concrete as the authors have claimed. I would agree with both of these assessments. As such, the authors are invited to revise the paper, if possible, to address these concerns.
]
#locations([Original decision letter])
#response[
We agree that the manuscript must state its limits more clearly. The revision narrows the claims to the two monitored groves, one overwintering season, the observed cluster sizes, and the measured wind metrics. We have also removed unsupported strong-evidence language and are recasting the physiological interpretation as a hypothesis for future testing. The final response will identify the revised title, Abstract, Discussion, and Conclusions locations after the line-numbered revised PDF is produced.
]

#heading(level: 2)[Length and statistical presentation]

#comment[
First, this manuscript is currently much too long, especially given the sample size issues noted above. The introduction takes forever to get through, for example. Also, there are 12 figures, and 5 tables, and the paper itself is 41 pages. Surely some of the more technical figures about the stats can be moved to an appendix. Also, there is some unnecessary discussion about monarch physiology later in the discussion, when this was not actually measured in the study.
]
#locations([Original decision letter])
#response[
We substantially compressed the statistical presentation so that the main article focuses on the two analyses that directly address the study question. We removed the simple linear regressions because they were redundant with the mixed-model analyses and did not account for the repeated-measures and temporal structure of the observations. We removed the fixed 24-hour sensitivity analysis because it addressed the same delayed-response question as the biologically aligned Next Day Window and did not add a distinct interpretation. We also removed the threshold-duration analysis because its exposure variable counted one-minute intervals containing a maximum gust at or above 2 m/s rather than the actual duration of exposure above that value. The retained manuscript now presents the immediate 30-minute and Next Day Window analyses. Code and generated outputs for the removed analyses remain available in the public repository. We are also reducing the introduction and recasting unmeasured physiology as a hypothesis for future testing. We will report the final page, figure, and table counts in the submitted version.
]

#heading(level: 2)[Western monarch decline framing]

#comment[
Second, there is much language in the paper and abstract about the dogmatic "decline" of the western monarch, which is based solely on counts of monarchs at the wintering colonies. This is a contentious issue, with many scientists now reporting how counts of monarchs in other life stages are not showing the same declines, or at least, they are not the same trajectory. Also, the messaging around the "decline" is now even thought to be the motivating factor behind the rise in non-native milkweed plantings, and captive-rearing of monarchs, both of which then give rise to greater infection prevalence of the OE parasite. The authors should consider how these statements have in itself, made things worse for monarchs. To address this main concern, the authors could simply remove the bits about the monarchs declining, and focus solely on the management implications for this work. Removing these would not detract from the main message of the paper, and, it would even help with the point above about length.
]
#locations([Original decision letter])
#response[
Draft in progress. We will remove or substantially reduce broad decline framing, state precisely what any remaining abundance statement measures, and keep the introduction focused on the study question and its management context.
]

#heading[Reviewer 1]

#heading(level: 2)[General comments]

#comment[
The manuscript entitled “Wind Does Not Disrupt Overwintering Monarch Butterfly Clusters: Direct Empirical Test of a Three-Decade Management Assumption” addresses an important conservation question and presents an interesting remote-monitoring approach. However, the main conclusions are broader than the study design and evidence can support. My principal concerns relate to the representativeness of the physical microenvironmental measurements, the limited spatial and temporal replication, and the extent to which the results support the proposed physiological mechanisms and management recommendations.

The analysis ultimately relies on two blue gum eucalyptus groves within the same military installation and a single effective overwintering season. In addition, wind was measured several meters from the clusters, solar irradiance was not measured directly, and several potentially relevant microclimatic variables were not monitored.

In my view, the study provides useful site-specific observational evidence, but it does not support a general rejection of the Wind Disruption Hypothesis. I therefore recommend major revision.

The points below should be addressed in the manuscript itself, not only in the response letter. The corresponding clarifications, limitations, reanalyses, and changes in interpretation need to be incorporated throughout the text.
]
#locations([Original reviewer report])
#response[
We appreciate this framing. Our revision responds in the manuscript itself and not only here. We are limiting claims to the monitored conditions, documenting or qualifying the measurement limitations, removing unsupported analyses, and reducing management and mechanistic claims. Each specific response below identifies the corresponding manuscript revision.
]

#heading(level: 2)[Comment 1]
#comment[
1. Lines 1–28, 163–186, and 939–963: Although this is an empirical field assessment, the design is observational and wind was not experimentally manipulated. Can the absence of an association under the monitored conditions support the categorical statement that wind does not disrupt overwintering clusters? Please revise the title, Simple Summary, Abstract, Discussion, and Conclusions so that the claims are restricted to the monitored sites, season, cluster sizes, and wind metrics.
]
#locations([Lines 1–28, 163–186, and 939–963])
#response[
Draft in progress. We will replace categorical language with language that reports whether we detected a consistent negative association under the monitored conditions. We will make that scope explicit in the title decision, Simple Summary, Abstract, Discussion, and Conclusions.
]

#heading(level: 2)[Comment 2]
#comment[
2. Lines 89–147: Is the historical framing fully supported by the cited references? The early studies cited here concern Mexican overwintering sites, whereas Leong studied western monarchs in California. It is also unclear whether Leong explicitly proposed a uniform environmental envelope across California groves or whether this represents a later interpretation of the Microclimate Hypothesis. Does reference [42] directly test the wind component of the hypothesis? Please clarify these distinctions and avoid attributing subsequent interpretations directly to the original studies.
]
#locations([Lines 89–147])
#response[
Draft in progress. We are auditing the cited historical sources and will distinguish evidence from Mexican and western monarch studies, what the original studies directly reported, and later interpretations of the Microclimate Hypothesis. We will not attribute an unsupported uniform environmental envelope or wind test to the original studies.
]

#heading(level: 2)[Comment 3]
#comment[
3. Lines 188–215: Are two blue gum eucalyptus groves within the same installation and one effective overwintering season sufficient to generalize the findings to other California groves or western monarch populations with different tree species, canopy structures, latitudes, coastal exposure, weather conditions, and cluster densities? Please clearly define the scope of inference and limit the claims accordingly throughout the manuscript.
]
#locations([Lines 188–215])
#response[
Draft in progress. We will define the scope as observational evidence from two blue gum eucalyptus groves on one installation during one effective overwintering season. We will state that replication across grove types, locations, seasons, and cluster densities is needed before broader inference.
]

#heading(level: 2)[Comment 4]
#comment[
4. Lines 217–263: The wind sensors were located 4–17 m horizontally from the clusters, but it is not clear that these measurements represent the wind actually experienced by butterflies within the canopy. Please report, for each deployment, the horizontal and vertical sensor–cluster distances, intervening vegetation, canopy position, sensor calibration, and any validation performed at the cluster location. Why was wind direction not considered? Without demonstrating the representativeness of these measurements, the actual wind exposure of the clusters remains uncertain.
]
#locations([Lines 217–263])
#response[
Draft in progress. We will report the available placement, calibration, canopy-context, and validation information for each deployment. We will explain the treatment of wind direction and explicitly qualify the sensor values as measurements near the monitored clusters rather than demonstrated within-canopy exposure at every butterfly position.
]

#heading(level: 2)[Comment 5]
#comment[
5. Lines 257–263 and 370–377: Is the ≥2 m/s threshold used in this study physically comparable with the wind metric used in the original studies underlying the Wind Disruption Hypothesis? The present analysis uses maximum one-minute gust values, but a brief gust within a minute is not equivalent to one complete minute of exposure above 2 m/s. Please clarify whether the historical threshold referred to sustained wind, average wind speed, maximum gust, or another metric, and reconsider the term “minutes above threshold” unless the actual duration above 2 m/s was measured.
]
#locations([Lines 257–263 and 370–377])
#response[
We agree that a one-minute sampling interval containing a maximum gust at or above 2 m/s does not measure the actual duration of exposure above 2 m/s. We therefore removed the threshold-duration analysis, its candidate-model appendix, and the associated claims. We retain the observed distribution of maximum gusts as descriptive context and now state explicitly that these measurements do not provide an exact test of sustained exposure above 2 m/s.
]

#heading(level: 2)[Comment 6]
#comment[
6. Lines 299–301, 348–353, and 429–447: Why was solar irradiance not measured directly using a radiometer or similar sensor? The number of butterflies visible in direct sunlight is not an independent physical measurement of irradiance because it also depends on cluster size, butterfly behavior, visibility, and canopy geometry. Could this partly reflect the response variable itself and affect the interpretation of the reported wind–sun interaction? Please revise the terminology and discuss this limitation explicitly.
]
#locations([Lines 299–301, 348–353, and 429–447])
#response[
Draft in progress. We will use the descriptive term “number of butterflies visible in direct sunlight,” not irradiance or light intensity. We will state that it is not an independent physical irradiance measurement and discuss the potential relationship between visibility, cluster size, behavior, canopy geometry, and the response variable.
]

#heading(level: 2)[Comment 7]
#comment[
7. Lines 315–323: Were the temperatures displayed by the cameras validated against calibrated environmental sensors? Camera temperature may be influenced by solar heating and may not represent the air temperature experienced by the cluster. In addition, humidity, vapor pressure deficit, precipitation, and surface wetness were not monitored. Could the omission of these variables limit the attribution of cluster changes specifically to wind? Please clarify and incorporate these limitations into the manuscript.
]
#locations([Lines 315–323])
#response[
The camera-temperature readings were not independently validated against calibrated environmental sensors. We now state in the Methods that these readings may reflect camera housing and local solar exposure as well as ambient air temperature, and we describe them as approximate local measurements. We also added this limitation to the Discussion because temperature participates in the selected 30-minute interaction. The displayed prediction temperatures therefore should not be interpreted as precise measurements of the air or body temperature experienced by individual butterflies. Humidity, vapor pressure deficit, precipitation, and surface wetness were not monitored. We acknowledge that these omitted conditions may covary with wind and butterfly behavior, so the observational design does not support attributing all visible cluster changes specifically to wind.
]

#heading(level: 2)[Comment 8]
#comment[
8. Lines 217–263 and 275–314: Could the broad BI categories of 1–9, 10–99, and 100–999, together with the use of minimum category values, mask moderate but biologically relevant changes in visible cluster size? Please report inter-observer agreement, validation against independent counts, and sensitivity analyses using alternative category values.

Could wind-induced movement of the cameras, poles, branches, foliage, or clusters also alter the apparent BI without butterflies actually leaving the cluster? Please clarify whether image displacement or changes in visibility were evaluated during high-wind periods.
]
#locations([Lines 217–263 and 275–314])
#response[
We agree that the broad categories and their numerical representation limit the precision of the Butterfly Index. Each image was classified once, and observers worked on non-overlapping image sets. The original design therefore does not permit a formal inter-observer agreement statistic or retrospective comparison with independent counts. We now state this limitation directly rather than treating an observer term in the model as evidence of agreement. All labelers used the same training guide and deployment-specific grid, and classifications were reviewed for common errors with corrections communicated across the labeling team, but this quality-control process did not create independent replicate classifications.

We conducted two retrospective sensitivity checks. First, adding observer as a fixed effect did not improve the 30-minute M16 fit (likelihood-ratio p = 0.957), and the three-way wind by temperature by direct-sun estimate and uncertainty were effectively unchanged. Second, we regenerated both retained datasets using the original category lower bounds (1, 10, 100), rounded geometric midpoints (3, 32, 316), rounded arithmetic midpoints (5, 55, 550), and category upper bounds (9, 99, 999). In the 30-minute analysis, the three-way interaction remained strongly supported under every mapping (all p values approximately 1.2e-9), and removing that interaction increased AIC by 34.74 to 34.85. The conditional wind patterns retained the same directions. In the Next Day Window, the selected M32 interaction also remained supported (p = 0.00083 to 0.00137), with adjusted R-squared values from 0.391 to 0.397. These analyses indicate that the retained statistical patterns do not depend on using category minima, but they do not replace a formal agreement or independent-count validation.

Each deployment was defined as an uninterrupted series from one fixed camera configuration. Camera removal for battery or memory-card servicing, or any change in camera position, ended that deployment and initiated a new deployment. Cameras were positioned with a clear, unobstructed view of the monitored cluster area, and labelers classified only butterflies that were visually available rather than estimating occluded individuals. Meaningful rotation or field-of-view displacement was therefore not an identified within-deployment source of BI change.

Wind-driven branch movement could nevertheless redistribute a visible aggregation among grid cells. For example, a cluster classified in one hundreds cell could temporarily span two tens cells without an equivalent change in abundance. We now identify this category-boundary jitter as a potential source of short-term 30-minute BI error. It may occur more often during windy periods and therefore cannot simply be assumed to average away. The alternative category-value sensitivities reduce concern that the selected interaction depends on category minima, but they cannot eliminate this split-and-merge mechanism. We have moderated the manuscript's measurement claims and interpret the response as change in visible BI rather than confirmed arrivals, departures, or dislodgment. We also plan to provide deployment time-lapse videos in the supplementary materials so readers can inspect the stable field of view and the nature of vegetation movement directly.
]

#heading(level: 2)[Comment 9]
#comment[
9. Lines 264–272 and 598–623: Because the equipment was repositioned to follow aggregations, can each deployment be considered biologically independent? Could the same cluster, or many of the same butterflies, contribute to multiple deployments? Please clarify the biological unit of replication.

In addition, can “site fidelity” be inferred from a single camera view when butterflies may move to an unmonitored branch or nearby tree without leaving the grove? Please revise this terminology unless grove-level persistence was directly monitored.
]
#locations([Lines 264–272 and 598–623])
#response[
We now define a deployment as the monitoring and time-series unit associated with one fixed camera configuration, cluster view, and wind sensor. Equipment servicing or repositioning ended the deployment and initiated a new one. Multiple deployments could monitor the same cluster area or include some of the same butterflies, so deployments should not be interpreted as independent biological populations. The models account for repeated observations within deployments and deployment-days, but the scope of inference remains the monitored time series at the two groves.

We agree that a single camera view cannot establish grove-level site fidelity or distinguish departure from movement to an unmonitored branch or nearby tree. We replaced “site fidelity analysis” with “Next Day Window analysis” and describe its response as change in the visible cluster between consecutive days. We likewise avoid interpreting BI changes as confirmed arrival, departure, or abandonment.
]

#heading(level: 2)[Comment 10]
#comment[
10. Lines 990–1089: Several candidate models appear to be duplicated, including M17/M20 and M41/M44, with equivalent duplications in the threshold analysis. Were these duplicate models included when calculating the Akaike weights? Please remove the duplicate candidates, repeat the affected analyses if necessary, and update the corresponding results and interpretations.

In addition, only 42 of the 78 Next Day Window models converged. Can the selected model be described as decisively supported when almost half of the proposed candidate set could not be fitted? Please report this issue in the main text and explain how the convergence failures affected model comparison and selection.
]
#locations([Lines 990–1089])
#response[
Thank you for identifying the duplicated candidates. Your comment prompted us to audit and repeat both retained candidate-model comparisons. During that audit, we identified a separate issue in the original model-selection workflow. The candidates had been fitted using restricted maximum likelihood, and AIC values were then extracted from those fits even though the candidates differed in their fixed-effect structures. Restricted-likelihood AIC values are not comparable under those conditions. We therefore repeated candidate comparison using maximum likelihood and then refitted each selected model using restricted maximum likelihood for coefficient estimates, uncertainty, and figures.

For the 30-minute analysis, we removed exact duplicate candidates M20 and M44 without renumbering the remaining candidates. We also removed observer as a redundant nested random effect because each deployment was classified by one observer. This left the M16 fixed-effect estimates unchanged and resolved the convergence warning previously recorded for M43. All 50 unique candidates produced rankable fits. The maximum-likelihood comparison selected M16 rather than the previously reported M50. We consequently replaced the affected 30-minute Methods, Results, tables, figures, and interpretation with results from M16 and its restricted-maximum-likelihood refit.

For the Next Day Window, we reconstructed the candidate set from the 74 formulas actually defined in the original analysis. Sixty-seven of 74 candidates produced rankable fits, and seven fits with convergence warnings were excluded from the ranking and Akaike-weight calculation. M32 remained the selected model after maximum-likelihood comparison and restricted-maximum-likelihood refitting. Its corrected Akaike weight was 0.614, rather than the previously reported 0.85, and the null baseline was second with a delta AICc of 3.58. We therefore retained M32 while moderating the strength-of-support language. The revised manuscript reports the candidate counts, unsuccessful-fit handling, corrected selection results, and updated interpretations for both response windows. Complete candidate formulas, fit outcomes, warnings, and rankings are provided in the supplementary and reproducibility materials.
]

#heading(level: 2)[Comment 11]
#comment[
11. Lines 388–397 and 811–819: What biologically meaningful change in the Butterfly Index or visible cluster size corresponds to an effect of 0.15 standard deviations on the transfrmed response scale? Please provide an interpretable equivalent.

In addition, how does the power analysis account for uncertainty associated with sensor position, BI classification, movement of cameras or vegetation, and limited site-level replication? Please moderate the statement of “strong evidence against the hypothesis” unless these sources of uncertainty are incorporated. The results appear more appropriately interpreted as a failure to detect a consistent effect under the monitored conditions.
]
#locations([Lines 388–397 and 811–819])
#response[
We agree that the simulation-based power analysis did not incorporate uncertainty associated with environmental sensor placement, Butterfly Index classification, image movement or visibility, and limited grove-level replication. Its standardized effect sizes also could not be translated confidently into biologically meaningful changes in visible cluster size. We therefore removed the power-analysis Methods subsection, Results subsection, table, and associated strong-evidence claims. We now interpret the results as a failure to detect a consistent wind-disruption effect under the monitored conditions.
]

#heading(level: 2)[Comment 12]
#comment[
12. Lines 705–713: How were dislodged butterflies on the ground systematically monitored? No ground-search area, sampling frequency, timing, or detection criteria are described. Please add the corresponding methodology or remove the absence of grounded butterflies as evidence against wind disruption.
]
#locations([Lines 705–713])
#response[
Draft in progress. We will either document the ground-search method with its area, timing, frequency, and detection criteria or remove the absence of grounded butterflies as evidence against wind disruption.
]

#heading(level: 2)[Comment 13]
#comment[
13. Lines 714–784 and 847–938: Thoracic temperature, solar irradiance, convective heat transfer, metabolic expenditure, and lipid depletion were not directly measured. Should the proposed thermoregulatory explanation therefore be presented as a hypothesis for future testing rather than as a demonstrated mechanism?

Likewise, can observations from two groves during one season justify recommendations to simplify wind buffers, increase wind access, open canopies, or selectively thin groves? These interventions were not experimentally evaluated and could modify several microclimatic variables simultaneously. Please substantially reduce the management recommendations and clearly present them as hypotheses requiring controlled evaluation.
]
#locations([Lines 714–784 and 847–938])
#response[
Draft in progress. We will describe thermoregulation as a possible explanatory hypothesis rather than a demonstrated mechanism because the relevant physiological variables were not measured. We will remove or substantially reduce prescriptive management recommendations and state that any canopy or wind-management intervention requires controlled, replicated evaluation.
]

#heading(level: 2)[Comment 14]
#comment[
14. Lines 975–977: Given the customized image-classification method, OCR procedure, Butterfly Index calculation, and extensive model-selection analyses, is making the data and analytical code available only upon request sufficient for reproducibility? Please deposit the processed data, metadata, classification protocol, model formulas, and analysis code in a permanent public repository.
]
#locations([Lines 975–977])
#response[
Draft in progress. We will prepare a permanent public archive for the processed data, metadata, classification and OCR protocol, model formulas, and analysis code. The final response will cite the archive DOI or persistent URL and the revised data-availability statement.
]

#heading(level: 2)[Minor comment 1]
#comment[
1. Lines 155–157: Herbicides are themselves pesticides. If “pesticide exposure” refers specifically to insecticides or other non-herbicide pesticides, please state this clearly to avoid redundancy.
]
#locations([Lines 155–157])
#response[
Draft in progress. We will revise the terminology so herbicides are not redundantly distinguished from pesticides, or specify the intended non-herbicide category where that distinction is necessary.
]

#heading[Reviewer 2]

#heading(level: 2)[Comment 1]
#comment[
1. In the “Materials and Methods”, I suggest adding pictures of the study sites. This would improve the visual presentation of the study and provide readers with a better understanding of the field conditions.
]
#locations([Original reviewer report])
#response[
Draft in progress. We will determine whether suitable photographs and permissions are available. If so, we will add a concise site figure that supports the Methods without increasing the manuscript’s technical burden.
]

#heading(level: 2)[Comment 2]
#comment[
2. Despite the relatively large sample volume (1,894 paired observations), the analysis is based on data collected during only one season and from only 2 study localities. This considerably limits the statistical robustness and generalizability of the results. I therefore believe that the conclusions should mention the need for further research conducted over multiple seasons and across a larger number of study sites.
]
#locations([Original reviewer report])
#response[
Draft in progress. We will state this limitation prominently and call for replicated work across seasons, study sites, grove structures, and weather conditions before generalizing beyond the monitored setting.
]

#heading(level: 2)[Comment 3]
#comment[
3. How representative are the wind-speed measurements taken at the apices of pole, considering that the wind speed within the tree canopy, where the butterfly aggregations were actually recorded, was evidently lower? This issue may be important when interpreting the relationship between wind conditions and butterfly aggregation. The authors should therefore discuss this potential limitation and clarify to what extent measurements taken above the canopy can be considered representative of the microclimatic conditions experienced by the butterflies.
]
#locations([Original reviewer report])
#response[
Draft in progress. We will provide the requested placement context and make clear that the measurements characterize the monitored environment near the clusters. We will not treat them as direct measurements of the wind experienced at every within-canopy butterfly position.
]

#heading(level: 2)[Comment 4]
#comment[
4. Habitat conservation is undoubtedly essential. However, the authors appear to extrapolate data obtained from only two study sites to current management recommendations based on wind-speed thresholds that “are not supported by empirical evidence.” In my opinion, this conclusion should be somewhat tempered and not generalized too broadly. The study represents a one-season investigation conducted at only two sites, and the authors did not examine different forest types, different population densities, or different geographic regions. Consequently, the available evidence is not yet sufficient to conclude that the existing management thresholds are broadly unsupported. It would be more appropriate to state that the present findings raise questions about the applicability or empirical support of these thresholds and highlight the need for further research across different habitats, population densities, seasons, geographic regions, etc.
]
#locations([Original reviewer report])
#response[
Draft in progress. We will temper this language and state that the findings raise questions about the applicability of wind-threshold guidance under the monitored conditions. We will call for direct, controlled work across habitats, population densities, seasons, and geographic regions before broader recommendations are made.
]

#heading[Final production checklist]

Before submission, we will complete the following production steps.

- Replace all pending revised locations with page and line references from the final line-numbered revised PDF.
- Update every response marked “Draft in progress” after its corresponding manuscript decision is complete.
- Confirm that the submitted response letter contains only finalized text and no internal issue links if the journal does not permit external links.
- Generate the clean revised manuscript from LaTeX.
- Generate a marked Word manuscript by comparing the original and revised Word renderings in Microsoft Word, then inspect all tracked changes.
- Export this response letter to PDF. A Word copy may also be generated from this Typst source if the journal requests it.
