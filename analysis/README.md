# Reproducing the manuscript

Run all commands from the repository root. The saved inputs and outputs are included, so you can inspect the results without installing the analysis software.

Install Python 3.13 or newer through [uv](https://docs.astral.sh/uv/) and restore the Python environment with `uv sync --locked`. Install R and the packages used by the scripts.

```sh
uv sync --locked
Rscript -e 'install.packages(c("dplyr", "ggplot2", "gratia", "here", "mgcv", "nlme", "patchwork", "purrr", "readr", "tibble"), repos="https://cloud.r-project.org")'
```

Python dependencies are recorded in [pyproject.toml](../pyproject.toml) and [uv.lock](../uv.lock). The R packages are not version locked. Regenerated plots or floating-point results can vary with package versions. The committed manuscript figures preserve the submitted versions.

The main analysis reads [analysis_30_minute.csv](../data/analysis_inputs/analysis_30_minute.csv) and [analysis_next_day.csv](../data/analysis_inputs/analysis_next_day.csv) directly. Their field names use BI, delta BI and explicit weather units. They contain 17 and 10 columns respectively. These inputs stay in the manuscript repository, separate from the observational release. Every column is used by a retained analysis, descriptive summary or the focused observer sensitivity. The signed square-root next-day response is calculated in R. The stored signed cube-root 30-minute response is preserved from the historical input.

This command regenerates descriptive summaries, the descriptive figure, wind-exceedance statistics, all 121 harmonized candidate fits and their selected models, and the Next Day figure and diagnostics.

```sh
Rscript analysis/run_results_analyses.R
```

[harmonized_model_comparison.R](harmonized_model_comparison.R) is the primary analysis for both response windows. Its [output guide](outputs/harmonized_model_comparison/README.md) explains the candidate sets and separately ranked sensitivities. [all_comparisons.csv](outputs/harmonized_model_comparison/all_comparisons.csv) records all attempted fits. [selected_models.csv](outputs/harmonized_model_comparison/selected_models.csv) records the selected formulas. The same directory contains rankings, coefficient summaries, fit statistics, conditional wind effects, and the 30-minute prediction figure.

[next_day_window_analysis.R](next_day_window_analysis.R) reads the selected primary Next Day formula from that comparison and refits it using restricted maximum likelihood for the manuscript interaction figure and residual diagnostics. Its [outputs](outputs/next_day_window/) use that selected model. Run the harmonized comparison first if regenerating the selection. The script no longer reruns the earlier candidate search or creates duplicate figures in the root figure directory.

[descriptive_statistics.R](descriptive_statistics.R) writes [descriptive summaries](outputs/descriptive_statistics/) for the two retained windows. It distinguishes paired rows from unique images. [descriptive_figures.R](descriptive_figures.R) generates the manuscript BI distribution and hourly change figure and its [summary tables](outputs/descriptive_figures/). [wind_at_clusters_statistics.R](wind_at_clusters_statistics.R) records the proportion of occupied 30-minute pairs with gusts at or above 2 m/s in [wind_at_clusters_summary.csv](outputs/wind_at_clusters/wind_at_clusters_summary.csv).

The larger CSVs directly under data retain the historical inputs and original variable names. Rebuild the reduced analysis inputs from those files without needing the portable photo drive with this command.

```sh
uv run analysis/prepare_data_release.py --analysis-only
```

To re-derive the historical inputs from source classifications, deployment metadata, wind records and temperature records, the original preparation commands remain available. Then run the analysis-only export so the R scripts receive the updated inputs. This is a separate operation from reproducing the committed analysis.

```sh
uv run analysis/prepare_lag_30min.py --lag-minutes 30 --tolerance-minutes 5 --output-file data/monarch_analysis_lag30min.csv
uv run analysis/prepare_dynamic_windows.py --output-nextday data/monarch_daily_lag_analysis_nextday_window.csv
uv run analysis/prepare_data_release.py --analysis-only
```

The focused BI category and observer sensitivity checks are a separate step. Their preparation script regenerates inputs under four category mappings, checks the lower-bound mapping against the historical inputs and exports each variant using the analysis schema. The observer check reads the 30-minute analysis table directly. The variant files are generated analysis intermediates and are not added to the data release.

```sh
uv run analysis/prepare_bi_category_sensitivity.py
Rscript analysis/bi_category_sensitivity_analysis.R
```

See the [sensitivity guide](outputs/bi_category_sensitivity/README.md) for methods and results. These are the submitted focused M16 and M32 checks. The 30-minute M16 sensitivity omits time since the first daily observation. The primary manuscript model includes time since the first daily observation, and its separately ranked no-time comparison is recorded in the harmonized outputs.

To regenerate the observational tables, native classification JSON copies, photo index, dictionary and draft XML, mount MonarchSSD and run `uv run analysis/prepare_data_release.py`. TGR1 release copies are prepared with `uv run --no-project tools/prepare_tgr1_photos.py`, which aligns image metadata to the deployment endpoints. The release builder reads the frozen reconciliation under `/Volumes/MonarchSSD/data_release/reconciled_2026-09-13`. It writes the public files to data/release and stages a matching package on the drive. Analysis inputs, scripts and working notes are outside the public package. Read the [release notes](../data/release/README.md) before using these draft products.

The September 13 schema migration reproduced all 121 candidate fits and all 34 checked result tables with zero numerical differences. The [verification report](../data/release_working/analysis_verification.json) normalizes only documented variable renames and the coverage-note wording. To repeat that comparison, save an outputs directory from the historical script run, run the updated scripts, then use `uv run analysis/verify_release_results.py /path/to/baseline_outputs`. Regression tests run with `uv run python -m unittest discover -s analysis -p 'test_release_schema.py'`.

The time adjustment was previously described as minutes since sunrise. Inspection of prepare_lag_30min.py shows that it is minutes since the first observation in the upstream deployment-day series. The CSV, model formulas and manuscript wording now use that definition. Its values and numerical model results are unchanged. Recorded device times are described in the release README and XML. The UTC parser in descriptive scripts is used only for arithmetic on the supplied clock readings, not to infer a UTC offset.

The [second-submission backup](https://github.com/kylenessen/monarch-wind-light-manuscript/tree/second-submission/analysis) preserves the earlier candidate searches, fixed 24-hour and threshold analyses, exploratory figures, and revision-era exports. They are no longer part of the current reproduction workflow.
