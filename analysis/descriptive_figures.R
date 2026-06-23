#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(readr)
  library(tibble)
  library(here)
})

out_dir <- here("analysis", "outputs", "descriptive_figures")
fig_dir <- here("figures")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

cfg <- list(
  dpi = 600,
  display_width = 6,
  target_axis_title = 12,
  target_axis_text = 10,
  figure_w = 7,
  figure_h = 5,
  steelblue = "steelblue",
  dark_gray = "#4d4d4d",
  zero_line = "gray65"
)

make_theme <- function(fig_width = cfg$figure_w) {
  scale_factor <- fig_width / cfg$display_width

  theme_minimal(base_size = round(cfg$target_axis_title * scale_factor)) +
    theme(
      panel.grid.major = element_line(color = "gray90", linewidth = 0.5),
      panel.grid.minor = element_blank(),
      axis.text = element_text(color = "black", size = round(cfg$target_axis_text * scale_factor)),
      axis.title = element_text(color = "black", size = round(cfg$target_axis_title * scale_factor)),
      plot.title = element_blank(),
      plot.subtitle = element_blank(),
      plot.caption = element_blank(),
      legend.position = "none"
    )
}

lag_data <- read_csv(here("data", "monarch_analysis_lag30min.csv"), show_col_types = FALSE) %>%
  filter(!is.na(butterfly_difference))

obs_t <- lag_data %>%
  transmute(
    deployment_id,
    image_filename = image_filename_t,
    timestamp = as.POSIXct(timestamp_t, tz = "UTC"),
    butterfly_index = total_butterflies_t
  )

obs_lag <- lag_data %>%
  transmute(
    deployment_id,
    image_filename = image_filename_t_lag,
    timestamp = as.POSIXct(timestamp_t_lag, tz = "UTC"),
    butterfly_index = total_butterflies_t_lag
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

ggsave(
  here("figures", "fig14_bi_distribution.png"),
  p_bi,
  width = cfg$figure_w,
  height = cfg$figure_h,
  dpi = cfg$dpi,
  bg = "white"
)

hourly_day_means <- lag_data %>%
  mutate(
    timestamp_t = as.POSIXct(timestamp_t, tz = "UTC"),
    hour = format(timestamp_t, "%H:00"),
    hour_num = as.integer(format(timestamp_t, "%H"))
  ) %>%
  filter(!is.na(hour), !is.na(deployment_day)) %>%
  group_by(deployment_day, hour, hour_num) %>%
  summarise(
    deployment_day_hour_mean = mean(butterfly_difference, na.rm = TRUE),
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
    y = expression(paste("Mean change in Butterfly Index (", Delta, "BI)"))
  ) +
  make_theme() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    panel.grid.major.x = element_blank(),
    plot.margin = margin(6, 12, 6, 8)
  )

ggsave(
  here("figures", "fig15_hourly_delta_bi.png"),
  p_hourly,
  width = cfg$figure_w,
  height = cfg$figure_h,
  dpi = cfg$dpi,
  bg = "white"
)

message("Wrote descriptive figure summaries to ", out_dir)
message("Updated Figure 14 and Figure 15 in ", fig_dir)
