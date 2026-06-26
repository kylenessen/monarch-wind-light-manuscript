#!/usr/bin/env Rscript

scripts <- c(
  "analysis/descriptive_statistics.R",
  "analysis/linear_regression_figures.R",
  "analysis/wind_at_clusters_histogram.R",
  "analysis/thirty_minute_gamm_analysis.R",
  "analysis/threshold_wind_disruption_analysis.R",
  "analysis/next_day_window_analysis.R",
  "analysis/twenty_four_hour_robustness_analysis.R"
)

for (script in scripts) {
  message("\nRunning ", script)
  status <- system2("Rscript", script)
  if (!identical(status, 0L)) {
    stop("Script failed: ", script, call. = FALSE)
  }
}

message("\nAll Results analysis scripts completed.")
