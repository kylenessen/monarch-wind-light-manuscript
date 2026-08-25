# M16 full output bundle

This directory contains the complete focused export for the selected 30-minute model M16. The model was selected by maximum-likelihood AIC comparison and refitted using restricted maximum likelihood for coefficient estimation.

The `tables` directory contains the fixed effects with confidence intervals, model-fit statistics, variance components, conditional wind effects, figure prediction values, and residual diagnostic statistics. The `text` directory contains the complete printed model output, figure conditions, and R session information.

The primary interpretation figures are `m16_predicted_response.png` and `m16_conditional_wind_effect.png`. They use representative observed conditions and the manuscript's existing figure style. The remaining figures show residual diagnostics, ACF, and PACF.

The raw main-effect coefficients should not be interpreted independently because M16 contains a three-way interaction and its predictors were not centered. In particular, the raw maximum-wind coefficient is conditional on temperature equal to zero, which falls outside the observed range. The prediction and conditional-effect figures provide the appropriate interpretation at observed temperatures and direct-sun counts.
