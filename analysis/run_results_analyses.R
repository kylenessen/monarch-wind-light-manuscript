#!/usr/bin/env Rscript

scripts <- c(
  "analysis/descriptive_statistics.R",
  "analysis/descriptive_figures.R",
  "analysis/wind_at_clusters_statistics.R",
  "analysis/harmonized_model_comparison.R",
  "analysis/next_day_window_analysis.R"
)

for (script in scripts) {
  message("\nRunning ", script)
  status <- system2("Rscript", script)
  if (!identical(status, 0L)) {
    stop("Script failed: ", script, call. = FALSE)
  }
}

message("\nAll Results analysis scripts completed.")
