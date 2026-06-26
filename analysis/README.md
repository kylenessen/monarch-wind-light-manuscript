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

`thirty_minute_gamm_analysis.R` refits the 52 30-minute GAMM candidates using the same random-effects structure as the publication figure script, writes model-selection outputs to `analysis/outputs/30_minute`, and regenerates `figures/partial_effects_30min.png`, `figures/interaction_wind_sun_30min.png`, `figures/diagnostics_30min.png`, and `figures/acf_30min.png`.

`threshold_wind_disruption_analysis.R` refits the 52 threshold GAMM candidates using the same random-effects structure as the publication figure script, writes model-selection outputs to `analysis/outputs/threshold`, and regenerates `analysis/outputs/threshold/figures/threshold_interaction_wind_sun.png`. This is a provenance figure, not a manuscript figure unless `manuscript.tex` includes it.

`next_day_window_analysis.R` refits the best Next Day Window model, writes summaries to `analysis/outputs/next_day_window`, and regenerates `figures/partial_effects_nextday.png`, `figures/interaction_wind_sun_nextday.png`, `figures/diagnostics_nextday.png`, and `figures/acf_nextday.png`. The retained full model-selection table is `analysis/outputs/next_day_window/model_comparison_comprehensive.csv`.

`twenty_four_hour_robustness_analysis.R` refits the 24-hour robustness model, writes summaries to `analysis/outputs/24_hour`, and regenerates `figures/interaction_wind_sun_24hr.png`.

`generate_publication_figures_all.R` is a convenience script that regenerates the manuscript figure set in one pass. Prefer the focused scripts above when tracing a specific result.
