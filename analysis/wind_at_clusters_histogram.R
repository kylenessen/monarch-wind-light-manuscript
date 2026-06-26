#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(readr)
  library(tibble)
  library(here)
})

out_dir <- here("analysis", "outputs", "wind_at_clusters")
fig_dir <- here("figures")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

cfg <- list(
  dpi = 600,
  figure_w = 6.5,
  figure_h = 4.0,
  binwidth = 0.25,
  threshold = 2,
  fill = "steelblue",
  threshold_color = "#c23b3b",
  dark_gray = "#4d4d4d"
)

make_theme <- function() {
  theme_minimal(base_size = 12) +
    theme(
      panel.grid.major = element_line(color = "gray90", linewidth = 0.5),
      panel.grid.minor = element_blank(),
      axis.text = element_text(color = "black"),
      axis.title = element_text(color = "black"),
      plot.title = element_blank(),
      plot.subtitle = element_blank(),
      plot.caption = element_blank()
    )
}

cluster_wind <- read_csv(here("data", "monarch_analysis_lag30min.csv"), show_col_types = FALSE) %>%
  filter(
    !is.na(max_gust),
    !is.na(total_butterflies_t),
    total_butterflies_t > 0
  )

wind_summary <- tibble(
  n_paired_rows = nrow(cluster_wind),
  minimum_max_gust = min(cluster_wind$max_gust, na.rm = TRUE),
  first_quartile_max_gust = quantile(cluster_wind$max_gust, 0.25, names = FALSE, na.rm = TRUE),
  median_max_gust = median(cluster_wind$max_gust, na.rm = TRUE),
  mean_max_gust = mean(cluster_wind$max_gust, na.rm = TRUE),
  third_quartile_max_gust = quantile(cluster_wind$max_gust, 0.75, names = FALSE, na.rm = TRUE),
  maximum_max_gust = max(cluster_wind$max_gust, na.rm = TRUE),
  n_at_or_above_2ms = sum(cluster_wind$max_gust >= cfg$threshold, na.rm = TRUE),
  percent_at_or_above_2ms = 100 * mean(cluster_wind$max_gust >= cfg$threshold, na.rm = TRUE)
)

write_csv(wind_summary, file.path(out_dir, "wind_at_clusters_summary.csv"))

histogram <- ggplot(cluster_wind, aes(x = max_gust)) +
  geom_histogram(
    binwidth = cfg$binwidth,
    boundary = 0,
    fill = cfg$fill,
    color = "white",
    linewidth = 0.25
  ) +
  geom_vline(
    xintercept = cfg$threshold,
    color = cfg$threshold_color,
    linetype = "dashed",
    linewidth = 0.8
  ) +
  annotate(
    "text",
    x = cfg$threshold + 0.15,
    y = Inf,
    label = "2 m/s",
    hjust = 0,
    vjust = 1.3,
    color = cfg$threshold_color,
    size = 3.5
  ) +
  scale_x_continuous(
    limits = c(0, ceiling(max(cluster_wind$max_gust, na.rm = TRUE))),
    breaks = seq(0, ceiling(max(cluster_wind$max_gust, na.rm = TRUE)), by = 2),
    expand = expansion(mult = c(0, 0.02))
  ) +
  labs(
    x = "Maximum wind gust speed (m/s)",
    y = "Frequency"
  ) +
  make_theme()

ggsave(
  here("figures", "wind_at_clusters_histogram.png"),
  histogram,
  width = cfg$figure_w,
  height = cfg$figure_h,
  dpi = cfg$dpi,
  bg = "white"
)

message("Wrote wind-at-clusters summary to ", out_dir)
message("Updated wind-at-clusters histogram in ", fig_dir)
