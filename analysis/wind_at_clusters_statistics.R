#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
  library(tibble)
  library(here)
})

out_dir <- here("analysis", "outputs", "wind_at_clusters")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

cluster_wind <- read_csv(here("data", "analysis_inputs", "analysis_30_minute.csv"), show_col_types = FALSE) %>%
  filter(
    !is.na(maximum_wind_gust_m_s),
    !is.na(current_bi),
    current_bi > 0
  )

wind_summary <- tibble(
  n_paired_rows = nrow(cluster_wind),
  minimum_max_gust = min(cluster_wind$maximum_wind_gust_m_s, na.rm = TRUE),
  first_quartile_max_gust = quantile(cluster_wind$maximum_wind_gust_m_s, 0.25, names = FALSE, na.rm = TRUE),
  median_max_gust = median(cluster_wind$maximum_wind_gust_m_s, na.rm = TRUE),
  mean_max_gust = mean(cluster_wind$maximum_wind_gust_m_s, na.rm = TRUE),
  third_quartile_max_gust = quantile(cluster_wind$maximum_wind_gust_m_s, 0.75, names = FALSE, na.rm = TRUE),
  maximum_max_gust = max(cluster_wind$maximum_wind_gust_m_s, na.rm = TRUE),
  n_at_or_above_2ms = sum(cluster_wind$maximum_wind_gust_m_s >= 2, na.rm = TRUE),
  percent_at_or_above_2ms = 100 * mean(cluster_wind$maximum_wind_gust_m_s >= 2, na.rm = TRUE)
)

write_csv(wind_summary, file.path(out_dir, "wind_at_clusters_summary.csv"))

message("Wrote wind-at-clusters summary to ", out_dir)
