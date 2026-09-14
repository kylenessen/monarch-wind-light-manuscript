#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(patchwork)
  library(readr)
  library(tibble)
  library(here)
})

source(here("analysis", "lib", "manuscript_figure_style.R"))

out_dir <- here("analysis", "outputs", "descriptive_figures")
fig_dir <- here("figures")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

cfg <- list(
  dpi = 600,
  include_width = 0.95,
  figure_w = 7,
  figure_h = 5,
  combined_w = 9,
  combined_h = 4.5,
  steelblue = "steelblue",
  dark_gray = "#4d4d4d",
  zero_line = "gray65"
)

make_theme <- function() {
  theme_like_reference(cfg$combined_w, cfg$include_width, grid_minor = FALSE) +
    theme(legend.position = "none")
}

lag_data <- read_csv(here("data", "release", "analysis_30_minute.csv"), show_col_types = FALSE) %>%
  filter(!is.na(delta_bi))

# UTC below is a neutral parser for clock arithmetic. It does not establish a UTC offset.
obs_t <- lag_data %>%
  transmute(
    deployment_id,
    image_filename = current_image_filename,
    timestamp = as.POSIXct(current_timestamp_recorded, tz = "UTC"),
    butterfly_index = current_bi
  )

obs_lag <- lag_data %>%
  transmute(
    deployment_id,
    image_filename = previous_image_filename,
    timestamp = as.POSIXct(previous_timestamp_recorded, tz = "UTC"),
    butterfly_index = previous_bi
  )

unique_observations <- bind_rows(obs_t, obs_lag) %>%
  distinct(deployment_id, image_filename, timestamp, .keep_all = TRUE) %>%
  filter(!is.na(butterfly_index))

bi_summary <- tibble(
  n_unique_observations = nrow(unique_observations),
  minimum_bi = min(unique_observations$butterfly_index, na.rm = TRUE),
  maximum_bi = max(unique_observations$butterfly_index, na.rm = TRUE),
  mean_bi = mean(unique_observations$butterfly_index, na.rm = TRUE),
  median_bi = median(unique_observations$butterfly_index, na.rm = TRUE)
)

write_csv(bi_summary, file.path(out_dir, "bi_distribution_summary.csv"))

p_bi <- ggplot(unique_observations, aes(x = butterfly_index)) +
  geom_histogram(
    binwidth = 25,
    boundary = 0,
    fill = cfg$steelblue,
    color = "white",
    linewidth = 0.25
  ) +
  labs(
    x = "Butterfly Index",
    y = "Frequency"
  ) +
  make_theme() +
  theme(
    panel.grid.major.x = element_blank(),
    plot.margin = margin(6, 12, 6, 8)
  )

hourly_day_means <- lag_data %>%
  mutate(
    current_timestamp_recorded = as.POSIXct(current_timestamp_recorded, tz = "UTC"),
    hour = format(current_timestamp_recorded, "%H:00"),
    hour_num = as.integer(format(current_timestamp_recorded, "%H"))
  ) %>%
  filter(!is.na(hour), !is.na(deployment_day_id)) %>%
  group_by(deployment_day_id, hour, hour_num) %>%
  summarise(
    deployment_day_hour_mean = mean(delta_bi, na.rm = TRUE),
    paired_rows = n(),
    .groups = "drop"
  )

hourly_summary <- hourly_day_means %>%
  group_by(hour, hour_num) %>%
  summarise(
    mean_delta_bi = mean(deployment_day_hour_mean, na.rm = TRUE),
    se_delta_bi = sd(deployment_day_hour_mean, na.rm = TRUE) / sqrt(n()),
    deployment_day_hours = n(),
    paired_rows = sum(paired_rows),
    .groups = "drop"
  ) %>%
  arrange(hour_num) %>%
  mutate(
    se_low = mean_delta_bi - se_delta_bi,
    se_high = mean_delta_bi + se_delta_bi,
    hour = factor(hour, levels = hour)
  )

write_csv(hourly_summary, file.path(out_dir, "hourly_delta_bi_summary.csv"))

p_hourly <- ggplot(hourly_summary, aes(x = hour, y = mean_delta_bi)) +
  geom_hline(yintercept = 0, color = cfg$zero_line, linewidth = 0.5) +
  geom_col(
    fill = cfg$steelblue,
    color = "white",
    linewidth = 0.25,
    width = 0.72
  ) +
  geom_errorbar(
    aes(ymin = se_low, ymax = se_high),
    width = 0.18,
    linewidth = 0.45,
    color = cfg$dark_gray
  ) +
  labs(
    x = "Time of day",
    y = expression(paste("Mean ", Delta, "BI"))
  ) +
  make_theme() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    panel.grid.major.x = element_blank(),
    plot.margin = margin(6, 12, 6, 8)
  )

combined_plot <- p_bi + p_hourly +
  plot_layout(ncol = 2) +
  plot_annotation(tag_levels = "A") &
  theme(
    plot.tag = element_text(
      face = "bold",
      size = reference_text_size(reference_figure_style$axis_title, cfg$combined_w, cfg$include_width)
    ),
    plot.tag.position = c(0.02, 0.98)
  )

ggsave(
  here("figures", "descriptive_bi.png"),
  combined_plot,
  width = cfg$combined_w,
  height = cfg$combined_h,
  dpi = cfg$dpi,
  bg = "white"
)

message("Wrote descriptive figure summaries to ", out_dir)
message("Updated descriptive BI figure in ", fig_dir)
