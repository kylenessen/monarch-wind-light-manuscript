#let c(n, body) = body
#set document(title: "Response to the Academic Editor and Reviewers")
#set page(paper: "us-letter", margin: (top: 0.78in, bottom: 0.78in, x: 0.82in))
#set text(font: "Libertinus Serif", size: 10.5pt, lang: "en")
#set par(leading: 0.62em, justify: true)
#set heading(numbering: none, outlined: true)
#set page(numbering: "1")

#let entry(title, concern, answer) = [
  #heading(level: 2)[#title]
  #block(
    fill: rgb("f2f5f7"),
    inset: 9pt,
    radius: 3pt,
    above: 0.55em,
    below: 0.35em,
    breakable: true,
  )[*Comment.* #concern]
  #block(
    stroke: (left: 1.2pt + rgb("2f6f70")),
    inset: (left: 10pt, right: 2pt, top: 2pt, bottom: 2pt),
    above: 0.15em,
    below: 0.65em,
    breakable: true,
  )[#text(weight: "bold", fill: rgb("1d5051"))[Response.] #answer]
]

#align(center)[
  #text(size: 17pt, weight: "bold")[Point-by-Point Response]
  #v(0.35em)
  #text(size: 13pt)[Response to the Academic Editor and Reviewers]
  #v(1em)
  *Revised manuscript title:* \
  _#c(1)[Wind Associations with Overwintering Monarch Butterfly Cluster Size Depend on Temperature and Sun Exposure]_
  #v(0.25em)
  *Journal:* _Insects_
]

#v(1.25em)

Dear Academic Editor and Reviewers,

Thank you for the careful and constructive reviews. The manuscript is substantially stronger because of this feedback. We shortened the paper and revised its analyses, interpretation, and scope. The revised title and all summary sections now describe conditional associations under the monitored conditions rather than a general or causal rejection of wind effects. We removed unsupported analyses and management recommendations, clarified the environmental and image-based measurements, repeated the candidate-model comparisons, added sensitivity analyses, and made the processed data and analytical materials public. The responses below address every comment. Manuscript sections are named directly because line numbers may change during journal production.

#heading[Academic Editor]

#entry(
  [Overall assessment],
  [The conclusions were too broad for observations from two localities during one effective field season.],
  [We agree. The revised manuscript consistently identifies the study as observational and limits inference to two blue gum eucalyptus groves, one overwintering season, the observed cluster sizes, and nearby maximum-gust measurements. We replaced the categorical title with “Wind Associations with Overwintering Monarch Butterfly Cluster Size Depend on Temperature and Sun Exposure.” The Simple Summary, Abstract, Discussion, and Conclusions now state that the predicted consistent decline was not detected under the monitored conditions. We also removed prescriptive habitat-management recommendations and added an explicit need for replication across seasons, sites, grove structures, cluster densities, and geographic regions.],
)

#entry(
  [Length and statistical presentation],
  [The manuscript was too long, contained too many technical figures and tables, and devoted too much discussion to physiology that was not measured.],
  [We substantially reduced the manuscript. We removed the simple linear regressions, the fixed 24-hour analysis, the threshold-duration analysis, and the simulation-based power analysis. We also removed their associated figures, tables, appendices, and discussion. The main text now focuses on our strongest results, the 30-minute and Next Day response windows, and contains four figures and no main-text tables. Technical formulas and candidate mappings are confined to the appendix and public reproducibility files. The physiology section is shorter and explicitly presents thermoregulation and energetic constraints as hypotheses for future testing, not demonstrated mechanisms.],
)

#entry(
  [Western monarch decline framing],
  [Broad statements about western monarch decline were contentious and distracted from the management question.],
  [We removed the population-decline framing from the Simple Summary, Abstract, Introduction, Discussion, and Conclusions. The revised Introduction is limited to the ecological and historical background needed to explain the motivation for the study and the wind-related prediction we evaluated.],
)

#heading[Reviewer 1]

#entry(
  [General comments],
  [The study provides useful site-specific observational evidence, but the environmental measurements, replication, physiological claims, and management recommendations did not support the original broad conclusions.],
  [We agree with this scope. The revision addresses these concerns in the manuscript itself. Claims are limited to the monitored setting, measurement limitations are stated in the Methods and Discussion, physiological explanations are framed as hypotheses, and broad management recommendations have been removed.],
)

#entry(
  [Comment 1. Observational design and categorical claims],
  [Revise the title and all summary sections so the claims are restricted to the monitored sites, season, cluster sizes, and wind metrics.],
  [We revised the title, Simple Summary, Abstract, final Introduction paragraph, Discussion, and Conclusions. The paper now reports that stronger nearby maximum gusts were not consistently followed by declines in visible cluster size under the monitored conditions. It does not state that wind cannot disrupt monarch clusters generally, and it does not describe wind as experimentally manipulated.],
)

#entry(
  [Comment 2. Historical framing],
  [Distinguish Mexican and California studies, separate original findings from later interpretations, and clarify which studies directly evaluated wind.],
  [We rewrote the historical section of the Introduction. It now distinguishes early physiological and weather studies from Mexico, occupied-versus-unoccupied microenvironment studies in central California, later qualitative wind accounts, and subsequent management guidance. It also states that the studies supporting the 2 m/s value did not directly quantify cluster responses during measured wind exposure. We no longer attribute a uniform California-wide environmental envelope or a direct wind test to the original studies.],
)

#entry(
  [Comment 3. Scope of inference],
  [Two eucalyptus groves on one installation during one season cannot support broad inference to other groves, populations, or conditions.],
  [We now define that scope in the Study Design, Discussion, and Conclusions. The Discussion further states that nearly all 30-minute observations came from one grove and that only Spring Canyon contributed to the Next Day analysis. The Conclusions call for replicated work across seasons, sites, grove structures, cluster densities, and regions to determine whether the result extends beyond the monitored setting.],
)

#entry(
  [Comment 4. Wind-sensor placement and representativeness],
  [Report placement, canopy context, calibration, validation, and treatment of wind direction for each deployment.],
  [The Monitoring System subsection now reports pole heights of 5.4 to 9.4 m and horizontal cluster distances of 4.2 to 16.5 m. Appendix A provides the recorded height, horizontal distance, and camera bearing for every analyzed deployment. Cluster heights, vertical sensor-to-cluster distances, intervening vegetation, and canopy positions were not recorded systematically, so we state that they cannot be reconstructed. We also state that the loggers were screened for gross abnormalities and compared during overlapping deployments but were not calibrated against a reference sensor or validated at butterfly positions. Wind direction was not analyzed because the focal historical prediction concerned wind-speed magnitude. Directional exposure at the butterflies also could not be inferred from a pole heading without measurements of the intervening canopy and its effects on airflow. Throughout the manuscript, the values are described as nearby pole-position measurements rather than within-canopy exposure at individual butterflies.],
)

#entry(
  [Comment 5. Historical threshold and gust metric],
  [A one-minute interval containing a maximum gust above 2 m/s is not equivalent to one minute of sustained exposure above that value.],
  [We agree. We removed the threshold-duration analysis, its model appendix, and all associated claims. The manuscript retains maximum gust as a descriptive and continuous predictor. Average wind speed, modal gust, gust variability, and maximum gust were strongly correlated, so they contained substantially overlapping information. We selected maximum gust as the most direct continuous metric for the disruption prediction evaluated here. The manuscript explicitly states that one-minute maximum-gust records near the clusters do not measure sustained exposure above 2 m/s at butterfly positions and therefore do not provide an exact test of the historical threshold formulation.],
)

#entry(
  [Comment 6. Direct sunlight and irradiance],
  [The number of visible butterflies in direct sunlight is not an independent measurement of solar irradiance and may be related to the response.],
  [We replaced irradiance-like terminology with “sun-exposed Butterfly Index,” or “sun-exposed BI.” This variable is defined as the BI subtotal from occupied image cells classified as receiving direct sunlight. The Methods and Discussion state that it is not a physical measurement of irradiance or light intensity and that it depends on visible cluster size, behavior, visibility, and canopy geometry. We therefore interpret the interaction as a conditional association involving sun-exposed BI, not an independent irradiance effect.],
)

#entry(
  [Comment 7. Camera temperature and unmeasured conditions],
  [Clarify temperature validation and the absence of humidity, vapor pressure deficit, precipitation, and surface-wetness measurements.],
  [The camera temperatures were not independently validated against calibrated environmental sensors. The Methods now describe them as approximate local measurements that may reflect camera housing and solar exposure as well as ambient air temperature. The Discussion notes that the displayed temperatures are not precise air or butterfly body temperatures. The study was designed specifically to evaluate the wind prediction while building on earlier work that measured a broader set of microclimate conditions. We now state explicitly that solar irradiance, humidity, vapor pressure deficit, precipitation, and surface wetness were not measured, and we avoid attributing visible cluster changes to wind alone.],
)

#entry(
  [Comment 8. Butterfly Index validation and image movement],
  [Address coarse BI categories, lower-bound coding, inter-observer agreement, independent counts, alternative category values, and wind-related changes in image position or visibility.],
  [We now define BI as an index of visible cluster size rather than a count of individual butterflies. Each deployment was classified once by one labeler, and observers classified non-overlapping image sets. Formal inter-observer agreement and retrospective validation against independent counts are therefore not possible, and the manuscript states this directly. Adding observer as a fixed effect did not improve the 30-minute fit (likelihood-ratio p = 0.957), but we present this only as a check for mean observer differences, not as an agreement statistic.

    We repeated both retained analyses using category lower bounds, rounded geometric midpoints, rounded arithmetic midpoints, and upper bounds. The 30-minute three-way interaction, its conditional directions, and the Next Day interaction remained supported under every mapping. The Methods, Results, and public reproducibility files report these checks.

    The cameras had unobstructed views of the monitored aggregation areas, and only visible butterflies were counted. The guyed poles remained stable and did not visibly move or rotate during the included deployments. Images affected by the few pole falls were excluded. Branch movement was present and was addressed by manual classification of every image under a shared protocol. Residual short-term classification noise remains possible when a visible group falls near a BI category boundary, so we continue to interpret the response as visible BI change rather than confirmed arrival, departure, or dislodgment.],
)

#entry(
  [Comment 9. Deployment independence and site fidelity],
  [Clarify the biological unit of replication and avoid inferring site fidelity from a single camera view.],
  [A deployment is now defined as an uninterrupted monitoring period with one pole position, fixed camera configuration, cluster view, and wind logger. Servicing or repositioning began a new deployment. Deployments are observation and time-series units, not independent biological populations, and multiple deployments may have included the same aggregation or individual butterflies. We removed “site fidelity” terminology and use “Next Day Window analysis.” A camera view cannot distinguish movement to an unmonitored branch or tree from departure, so the response is described only as change in visible cluster size between days.],
)

#entry(
  [Comment 10. Duplicate candidates and convergence],
  [Remove duplicate candidates, repeat affected analyses, and explain how the original Next Day convergence failures affected inference.],
  [Thank you for identifying the duplicated candidates. Your comment prompted a complete audit and repetition of both retained comparisons. The audit also identified a separate problem in the original workflow. Candidates with different fixed-effect structures had been ranked using AIC values from restricted maximum-likelihood fits. We corrected this by comparing candidates with maximum likelihood and AICc, then refitting selected formulas with restricted maximum likelihood for estimates, uncertainty, figures, and diagnostics.

    We removed the exact duplicates and did not retain the incomplete original rankings. We replaced the window-specific candidate lists with a shared set of environmental hypothesis templates while preserving the window-specific predictor definitions. The primary 30-minute comparison contains 17 candidates. Separate 17-model sensitivities omit previous BI and time since sunrise. The primary Next Day comparison contains 35 candidates, and its 35-model sensitivity omits previous-day BI. All 121 fits converged without warnings.

    The corrected 30-minute best model changed to a three-way interaction among wind, temperature, and sun-exposed BI. We updated the Results, figures, and interpretation accordingly. The Next Day best model remained a wind by sun-exposed BI interaction, although its support was less decisive after correction. The overall result remains that wind alone did not predict a consistent decline in visible cluster size. Its association depended on temperature and direct sun exposure. We believe the corrected analysis and more transparent treatment of uncertainty make the paper stronger. The revised Methods, Results, appendices, and public output tables provide the full statistical details.],
)

#entry(
  [Comment 11. Power analysis and inferential strength],
  [Translate the standardized effect into biologically meaningful BI change and account for measurement and replication uncertainty, or moderate the claim.],
  [We agree that the simulation-based power analysis did not include key measurement and replication uncertainties and that its standardized effects could not be translated confidently into meaningful visible-cluster changes. We removed the power-analysis Methods, Results, table, and “strong evidence” language. The revised interpretation is that we did not detect the predicted consistent wind-disruption pattern under the monitored conditions.],
)

#entry(
  [Comment 12. Grounded butterflies],
  [Document systematic ground searches or remove the absence of grounded butterflies as evidence.],
  [We removed the claim that no grounded butterflies were observed and do not use ground observations as evidence against wind disruption.],
)

#entry(
  [Comment 13. Physiological mechanisms and management],
  [Present unmeasured physiological processes as hypotheses and reduce management recommendations that were not experimentally evaluated.],
  [We shortened the physiological discussion and explicitly state that thermoregulation and energetic constraints are possible explanations for future testing. The study did not measure irradiance, thoracic temperature, convective heat transfer, metabolic expenditure, lipid depletion, or movement among roosts. We removed all management recommendations. The manuscript now reports what we observed, offers a possible physiological explanation, and states that we did not find evidence that a single wind threshold consistently predicted declines in visible cluster size under the monitored conditions.],
)

#entry(
  [Comment 14. Public reproducibility materials],
  [Deposit processed data, metadata, protocols, model formulas, and code in a permanent public repository rather than making them available only on request.],
  [We changed the Data Availability statement and made the version-controlled repository public at #link("https://github.com/kylenessen/monarch-wind-light-manuscript")[github.com/kylenessen/monarch-wind-light-manuscript]. It contains processed data, deployment metadata, image classifications, analysis code, candidate formulas, fit outcomes, selected-model summaries, sensitivity outputs, and generated figures. The illustrated classification protocol is public at #link("https://kylenessen.github.io/monarch_trailcam_classifier/")[kylenessen.github.io/monarch_trailcam_classifier]. The repository also documents the OCR and manual-review procedure and preserves the reviewed image-derived temperature values. The original OCR extraction utility is not part of the repository, and we state this rather than claiming it is available. Raw images and the classification review software remain available from the corresponding author because a long-term public host has not been established. A DOI-backed archive of the final repository release will be created before publication.],
)

#entry(
  [Minor comment 1. Pesticide terminology],
  [Herbicides are pesticides, so the original wording was redundant.],
  [The sentence containing this distinction was removed when the Introduction was shortened. No herbicide-versus-pesticide wording remains in the revised manuscript.],
)

#heading[Reviewer 2]

#entry(
  [Comment 1. Study-site photographs],
  [Add photographs to help readers understand field conditions.],
  [We added a three-panel figure to the Materials and Methods. It shows the monitoring pole within a blue gum eucalyptus grove, the wind logger and camera positioned near an aggregation, and a representative near-infrared image used for BI classification.],
)

#entry(
  [Comment 2. One season and two localities],
  [State the limited generalizability and the need for work across more sites and seasons.],
  [We now state this limitation in the Study Design, Discussion, and Conclusions. The Conclusions call for replicated research across seasons, sites, grove structures, cluster densities, weather conditions, and regions before drawing broader inferences.],
)

#entry(
  [Comment 3. Representativeness of wind measurements],
  [Clarify whether pole-apex measurements represent wind within the canopy at butterfly positions.],
  [We agree that equivalence cannot be assumed. The Methods and Appendix report the available placement information and the measurements that were not recorded. The Discussion states that wind was measured near the clusters but not validated within the canopy at butterfly positions. All results are therefore framed as associations with nearby pole-position maximum gusts, not direct measurements of the wind experienced by each butterfly.],
)

#entry(
  [Comment 4. Management thresholds and generalization],
  [Temper the claim that existing thresholds are broadly unsupported and call for wider replication.],
  [We removed the management recommendations and revised the Conclusions. The manuscript now states that we did not find evidence that a single wind threshold consistently predicted declines in visible cluster size under the monitored conditions. It calls for replicated work across habitats, densities, seasons, and regions to determine whether this result extends beyond the monitored setting.],
)

#v(0.8em)

We again thank the Academic Editor and both reviewers. Their comments led to a shorter, more transparent manuscript with narrower claims, corrected model comparisons, clearer measurement limitations, and stronger reproducibility materials.

Sincerely,

Kyle Nessen, Peter C. Ibsen, Jay E. Diffendorfer, and Francis X. Villablanca
