# Manuscript analysis inputs

These two tables contain the exact inputs used by the R analysis scripts.
analysis_30_minute.csv contains 1,894 image pairs. analysis_next_day.csv contains
96 consecutive-day pairs. They are part of the manuscript repository and are
separate from the observational data release.

Run `Rscript analysis/run_results_analyses.R` from the repository root to reproduce
the main results. The [analysis guide](../../analysis/README.md) describes the
focused sensitivity analyses and software setup.

To regenerate these tables from the historical inputs stored directly under data,
run `uv run analysis/prepare_data_release.py --analysis-only`. This selects and
renames the retained fields without recomputing measurements. The column mapping
is recorded in [release_schema.py](../../analysis/release_schema.py).
