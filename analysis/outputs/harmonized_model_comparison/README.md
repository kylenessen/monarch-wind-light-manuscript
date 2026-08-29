# Harmonized Model Comparison

This directory contains the shared candidate-model comparison for the 30-minute and Next Day response windows. The same environmental hypothesis templates are applied to the window-specific predictors. Mean overnight temperature is not included in the Next Day candidate set.

The 30-minute primary framework includes previous BI and linear minutes since sunrise in every model. Its separately ranked sensitivities omit previous BI and omit time since sunrise. The Next Day primary framework includes previous-day maximum BI and window duration in every model. Its sensitivity omits previous-day maximum BI but retains window duration.

The shared templates include adjustments only, wind, sun-exposed BI, additive and linear interactive wind and sun effects, a centered tensor wind by sun interaction, its hierarchical counterpart with marginal smooths, additive temperature hypotheses, every linear two-way interaction, a full linear three-way interaction, and matched smooth hypotheses. The Next Day comparison repeats every temperature-dependent hypothesis for minimum temperature, maximum temperature, and temperature at the previous maximum BI.

All candidates are fitted using maximum likelihood and ranked by AICc. Akaike weights are calculated separately within each window and control framework. Selected models are refitted using restricted maximum likelihood. All 121 attempted fits completed without convergence warnings.

In the primary 30-minute framework, the full linear three-way interaction ranked first with AICc 8052.02 and an Akaike weight greater than 0.9999. The same environmental structure ranked first after omitting previous BI and after omitting time since sunrise.

In the primary Next Day framework, the centered wind by sun-exposed BI tensor interaction ranked first with AICc 650.01 and an Akaike weight of 0.368. The maximum-temperature-only model was within two AICc units. The three-way model using temperature at the previous maximum BI ranked third with a delta AICc of 2.99. Without previous BI, the centered tensor remained first, while the maximum-temperature three-way interaction was within one AICc unit.

The random-effect and correlation structures follow the repeated-measures hierarchy available in each dataset. The 30-minute models include random intercepts for deployment and deployment-day with AR(1) correlation within deployment-day. Next Day models include a deployment random intercept with AR(1) correlation within deployment. Observer is not included because observer does not vary independently within deployment and therefore cannot be separated from the deployment effect.
