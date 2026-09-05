# Reproducing the manuscript

Run all commands from the repository root. The saved inputs and outputs are included, so you can inspect the results without installing the analysis software.

Install Python 3.13 or newer through [uv](https://docs.astral.sh/uv/) and restore the Python environment with `uv sync --locked`. Install R and the packages used by the scripts.

```sh
uv sync --locked
Rscript -e 'install.packages(c("dplyr", "ggplot2", "gratia", "here", "mgcv", "nlme", "patchwork", "purrr", "readr", "tibble"), repos="https://cloud.r-project.org")'
```

Python dependencies are recorded in [pyproject.toml](../pyproject.toml) and [uv.lock](../uv.lock). The R packages are not version locked. Regenerated plots or floating-point results can vary with package versions. The committed manuscript figures preserve the submitted versions.

The main analysis uses the two committed datasets in [data/](../data/README.md). This command regenerates descriptive summaries, the descriptive figure, wind-exceedance statistics, all 121 harmonized candidate fits and their selected models, and the Next Day figure and diagnostics.

```sh
Rscript analysis/run_results_analyses.R
```

[harmonized_model_comparison.R](harmonized_model_comparison.R) is the primary analysis for both response windows. Its [output guide](outputs/harmonized_model_comparison/README.md) explains the candidate sets and separately ranked sensitivities. [all_comparisons.csv](outputs/harmonized_model_comparison/all_comparisons.csv) records all attempted fits. [selected_models.csv](outputs/harmonized_model_comparison/selected_models.csv) records the selected formulas. The same directory contains rankings, coefficient summaries, fit statistics, conditional wind effects, and the 30-minute prediction figure.

[next_day_window_analysis.R](next_day_window_analysis.R) reads the selected primary Next Day formula from that comparison and refits it using restricted maximum likelihood for the manuscript interaction figure and residual diagnostics. Its [outputs](outputs/next_day_window/) use that selected model. Run the harmonized comparison first if regenerating the selection. The script no longer reruns the earlier candidate search or creates duplicate figures in the root figure directory.

[descriptive_statistics.R](descriptive_statistics.R) writes [descriptive summaries](outputs/descriptive_statistics/) for the two retained windows. It distinguishes paired rows from unique images. [descriptive_figures.R](descriptive_figures.R) generates the manuscript BI distribution and hourly change figure and its [summary tables](outputs/descriptive_figures/). [wind_at_clusters_statistics.R](wind_at_clusters_statistics.R) records the proportion of occupied 30-minute pairs with gusts at or above 2 m/s in [wind_at_clusters_summary.csv](outputs/wind_at_clusters/wind_at_clusters_summary.csv).

To rebuild the two analysis inputs from the source classifications, deployment metadata, wind records, and temperature records, run these commands before the R analysis.

```sh
uv run analysis/prepare_lag_30min.py --lag-minutes 30 --tolerance-minutes 5 --output-file data/monarch_analysis_lag30min.csv
uv run analysis/prepare_dynamic_windows.py --output-nextday data/monarch_daily_lag_analysis_nextday_window.csv
```

The focused BI category and observer sensitivity checks are a separate step. Their preparation script regenerates inputs under four category mappings and checks the lower-bound mapping against the committed inputs.

```sh
uv run analysis/prepare_bi_category_sensitivity.py
Rscript analysis/bi_category_sensitivity_analysis.R
```

See the [sensitivity guide](outputs/bi_category_sensitivity/README.md) for methods and results. These are the submitted focused M16 and M32 checks. The 30-minute M16 sensitivity omits time since sunrise. The primary manuscript model includes time since sunrise, and its separately ranked no-time comparison is recorded in the harmonized outputs.

To regenerate the draft open-format release tables and field dictionary, run `uv run analysis/prepare_data_release.py`. Read the [release notes](../data/release/README.md) before using those tables as a release product.

The [second-submission backup](https://github.com/kylenessen/monarch-wind-light-manuscript/tree/second-submission/analysis) preserves the earlier candidate searches, fixed 24-hour and threshold analyses, exploratory figures, and revision-era exports. They are no longer part of the current reproduction workflow.
