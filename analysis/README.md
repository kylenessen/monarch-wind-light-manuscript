# Results Directory

This directory contains the analysis scripts and outputs used by the Results section of `manuscript.tex`.

Run Python data preparation scripts with `uv`. Run R scripts with `Rscript` from the repository root.

## Data Preparation

`prepare_lag_30min.py` regenerates `data/monarch_analysis_lag30min.csv` from deployment JSON, temperature CSV, wind SQLite databases, and deployment metadata.

```sh
uv run analysis/prepare_lag_30min.py --lag-minutes 30 --tolerance-minutes 5 --output-file data/monarch_analysis_lag30min.csv
```

`prepare_dynamic_windows.py` regenerates both daily window datasets.

```sh
uv run analysis/prepare_dynamic_windows.py --output-24hr data/monarch_daily_lag_analysis_24hr_window.csv --output-nextday data/monarch_daily_lag_analysis_nextday_window.csv
```

## Analysis Scripts

`descriptive_statistics.R` writes descriptive summaries to `analysis/outputs/descriptive_statistics`. It records both paired-row counts and unique-image counts because those denominators differ.

`descriptive_figures.R` regenerates the two-panel descriptive BI distribution and hourly 30-minute $\Delta$BI figure in `figures/`, and writes figure summaries to `analysis/outputs/descriptive_figures`.

`linear_regression_figures.R` regenerates the manuscript figure `figures/wind_linear_combined.png` and writes `analysis/outputs/linear_regression/linear_regression_summary.csv`.

`wind_at_clusters_histogram.R` regenerates the manuscript figure `figures/wind_at_clusters_histogram.png` and writes `analysis/outputs/wind_at_clusters/wind_at_clusters_summary.csv`. The figure uses current 30-minute paired rows where butterflies are present at time `t`, with 0.25 m/s bins.

`thirty_minute_gamm_analysis.R` compares the 50 unique 30-minute GAMM candidates using maximum likelihood, then refits the selected model using restricted maximum likelihood. It preserves the original candidate identifiers after removing duplicate models M20 and M44. The script writes a complete fit audit and model-selection outputs to `analysis/outputs/30_minute`. It regenerates model diagnostics and only generates a wind by direct-sun interaction surface when the selected model contains that tensor interaction.

`m16_prediction_support.py` calculates deployment-balanced central halfspace-depth regions for the M16 predictor combinations. Run it with `uv run analysis/m16_prediction_support.py`. `m16_full_outputs.R` then produces the complete focused export for the selected 30-minute M16 model. It writes fixed effects with confidence intervals, ML and REML fit statistics, variance components, conditional wind effects, full printed output, residual diagnostics, and manuscript-styled interpretation figures to `analysis/outputs/30_minute/m16`.

`prepare_bi_category_sensitivity.py` and `bi_category_sensitivity_analysis.R` regenerate both retained analyses using lower-bound, geometric-midpoint, arithmetic-midpoint, and upper-bound values for the ordinal BI categories. They also record a focused observer fixed-effect sensitivity check. Outputs are written to `analysis/outputs/bi_category_sensitivity`.

`threshold_wind_disruption_analysis.R` refits the 52 threshold GAMM candidates using the same random-effects structure as the publication figure script, writes model-selection outputs to `analysis/outputs/threshold`, and regenerates `analysis/outputs/threshold/figures/threshold_interaction_wind_sun.png`. This is a provenance figure, not a manuscript figure unless `manuscript.tex` includes it.

`next_day_window_analysis.R` reconstructs and compares the 74 Next Day Window candidates that were defined in the original analysis. These are M1 through M72 and M77 through M78. It uses maximum likelihood and AICc for comparison, records every fit and convergence warning, and refits the selected model using restricted maximum likelihood. Outputs are written to `analysis/outputs/next_day_window`, including the complete audit in `model_comparison_comprehensive.csv`.

`twenty_four_hour_robustness_analysis.R` refits the 24-hour robustness model, writes summaries to `analysis/outputs/24_hour`, and regenerates `figures/interaction_wind_sun_24hr.png`.

`generate_publication_figures_all.R` is a convenience script that regenerates the manuscript figure set in one pass. Prefer the focused scripts above when tracing a specific result.

## Figure Paths and Revision Status

The `figures/` directory contains files used directly by the current `manuscript.tex` build. The `analysis/outputs/` directories contain analysis-specific exports and provenance figures. The revised 30-minute M16 interpretation figures are in `analysis/outputs/30_minute/m16/figures`.

The current M16 interpretation figures are `m16_predicted_response.png` and `m16_conditional_wind_effect.png`. They show predicted responses and conditional wind effects at observed temperature and direct-sun conditions. The M16 diagnostics are `m16_diagnostics.png`, `m16_residual_acf.png`, and `m16_residual_pacf.png`.

The root files `figures/diagnostics_30min.png` and `figures/acf_30min.png` currently match the M16 diagnostics byte for byte. The root files `figures/partial_effects_30min.png` and `figures/interaction_wind_sun_30min.png` are legacy M50 figures. They remain in place because the current manuscript still references them. They should be replaced or removed only as part of the manuscript figure rewrite.

The Next Day Window files are mirrored between `figures/` and `analysis/outputs/next_day_window/figures`. These pairs currently match byte for byte. The 24-hour, threshold, and linear-regression figures are retained analysis outputs or legacy provenance files. They are not referenced by the current manuscript, but their generating scripts still write them. Do not delete them until those scripts and any supplemental-material decision are resolved.

Several mirrored files are exact duplicates. The current duplicate pairs are `figures/diagnostics_30min.png` with `analysis/outputs/30_minute/m16/figures/m16_diagnostics.png`, `figures/acf_30min.png` with `analysis/outputs/30_minute/m16/figures/m16_residual_acf.png`, the four Next Day Window figures with their counterparts in `analysis/outputs/next_day_window/figures`, and the 24-hour interaction figure with its counterpart in `analysis/outputs/24_hour/figures`. These duplicates are intentionally preserved because the focused scripts write the output copies and the manuscript build reads the root copies.

The convenience script `generate_publication_figures_all.R` still fits and labels the former M50 30-minute model. It is therefore a legacy generator until it is updated for M16. Use `thirty_minute_gamm_analysis.R` and `m16_full_outputs.R` when tracing the revised 30-minute analysis.
