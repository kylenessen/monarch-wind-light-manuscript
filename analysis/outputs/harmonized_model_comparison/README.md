# Harmonized Model Comparison

This directory contains the shared candidate-model comparison for the 30-minute and Next Day response windows. The analysis retains the environmental predictor definitions from the original window-specific analyses. It does not introduce mean overnight temperature into the Next Day candidate set.

The primary framework includes previous BI as a fixed linear adjustment in both windows. Next Day models also include window duration because the response windows vary from 24.0 to 34.7 hours. The separately ranked no-previous-BI frameworks repeat the same environmental hypotheses without the previous-BI adjustment. The 30-minute time-adjusted sensitivity repeats the full candidate set with linear time within day included in every model.

The two windows use a shared set of hypothesis templates. These include controls only, wind, sun-exposed BI, additive and linear interactive wind and sun effects, the tensor wind by sun interaction used by legacy model M32, its hierarchical counterpart with marginal smooths, additive temperature hypotheses, every linear two-way interaction, the full linear three-way interaction used by legacy model M16, and matched smooth hypotheses. The Next Day comparison repeats every temperature-dependent hypothesis for minimum temperature, maximum temperature, and temperature at the previous maximum BI. These are the temperature predictors from the original analysis.

All candidates are fitted using maximum likelihood and ranked by AICc. Akaike weights are calculated separately within each window and control framework. Selected models are refitted using restricted maximum likelihood. All 121 attempted fits completed without convergence warnings.

In the primary 30-minute framework, the exact M16 formula ranked first with AICc 8054.14 and an Akaike weight greater than 0.9999. It also ranked first without previous BI and after adding time within day to every candidate.

In the primary Next Day framework, the exact M32 formula ranked first with AICc 650.01 and an Akaike weight of 0.368. The maximum-temperature-only model was within two AICc units. The closest mirror of M16 used temperature at the previous maximum BI and ranked third with a delta AICc of 2.99. Without previous BI, M32 remained first, while the maximum-temperature three-way mirror was within one AICc unit.

The random-effect and correlation structures follow the repeated-measures hierarchy available in each dataset. The 30-minute models include random intercepts for deployment and deployment-day with AR(1) correlation within deployment-day. Next Day models include a deployment random intercept with AR(1) correlation within deployment. Observer is not included because observer does not vary independently within deployment and therefore cannot be separated from the deployment effect.
