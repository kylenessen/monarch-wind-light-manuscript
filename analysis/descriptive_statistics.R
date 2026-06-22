#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
  library(tibble)
  library(here)
})

out_dir <- here("analysis", "outputs", "descriptive_statistics")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

round_value <- function(x, digits = 3) {
  if (is.numeric(x)) {
    return(round(x, digits))
  }
  x
}

metric <- function(section, name, value, denominator = NA_character_, note = NA_character_) {
  tibble(
    section = section,
    metric = name,
    value = as.character(round_value(value)),
    denominator = denominator,
    note = note
  )
}

summarise_numeric <- function(data, column, section, label) {
  x <- data[[column]]
  bind_rows(
    metric(section, paste(label, "minimum"), min(x, na.rm = TRUE)),
    metric(section, paste(label, "maximum"), max(x, na.rm = TRUE)),
    metric(section, paste(label, "mean"), mean(x, na.rm = TRUE)),
    metric(section, paste(label, "standard deviation"), sd(x, na.rm = TRUE)),
    metric(section, paste(label, "median"), median(x, na.rm = TRUE)),
    metric(section, paste(label, "first quartile"), as.numeric(quantile(x, 0.25, na.rm = TRUE))),
    metric(section, paste(label, "third quartile"), as.numeric(quantile(x, 0.75, na.rm = TRUE)))
  )
}

lag_data <- read_csv(here("data", "monarch_analysis_lag30min.csv"), show_col_types = FALSE)

obs_t <- lag_data %>%
  transmute(
    deployment_id,
    image_filename = image_filename_t,
    timestamp = as.POSIXct(timestamp_t, tz = "UTC"),
    total_butterflies = total_butterflies_t,
    butterflies_direct_sun = butterflies_direct_sun_t,
    temperature = temperature_t
  )

obs_lag <- lag_data %>%
  transmute(
    deployment_id,
    image_filename = image_filename_t_lag,
    timestamp = as.POSIXct(timestamp_t_lag, tz = "UTC"),
    total_butterflies = total_butterflies_t_lag,
    butterflies_direct_sun = butterflies_direct_sun_t_lag,
    temperature = temperature_t_lag
  )

unique_obs <- bind_rows(obs_t, obs_lag) %>%
  distinct(deployment_id, image_filename, timestamp, .keep_all = TRUE) %>%
  mutate(
    date = as.Date(timestamp),
    hour = format(timestamp, "%H:00")
  )

deployment_day_hours <- unique_obs %>%
  group_by(deployment_id, date) %>%
  summarise(hours_between_first_and_last = as.numeric(difftime(max(timestamp), min(timestamp), units = "hours")), .groups = "drop")

hour_counts_unique <- unique_obs %>%
  count(hour, name = "unique_observations") %>%
  arrange(desc(unique_observations), hour)

hour_counts_paired_t <- lag_data %>%
  mutate(hour = format(as.POSIXct(timestamp_t, tz = "UTC"), "%H:00")) %>%
  count(hour, name = "paired_time_t_rows") %>%
  arrange(desc(paired_time_t_rows), hour)

per_deployment_bi <- unique_obs %>%
  group_by(deployment_id) %>%
  summarise(
    mean_bi = mean(total_butterflies, na.rm = TRUE),
    maximum_bi = max(total_butterflies, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  arrange(deployment_id)

next_day <- read_csv(here("data", "monarch_daily_lag_analysis_sunset_window.csv"), show_col_types = FALSE) %>%
  filter(metrics_complete >= 0.95)

hr24 <- read_csv(here("data", "monarch_daily_lag_analysis_24hr_window.csv"), show_col_types = FALSE) %>%
  filter(metrics_complete >= 0.95)

metrics <- bind_rows(
  metric("30-minute pairs", "paired rows", nrow(lag_data)),
  metric("30-minute pairs", "unique observation frames", nrow(unique_obs)),
  metric("30-minute pairs", "first observation date", as.character(min(unique_obs$date))),
  metric("30-minute pairs", "last observation date", as.character(max(unique_obs$date))),
  metric("30-minute pairs", "inclusive calendar days", as.numeric(max(unique_obs$date) - min(unique_obs$date)) + 1),
  metric("30-minute pairs", "deployment day combinations", n_distinct(paste(unique_obs$deployment_id, unique_obs$date))),
  metric("30-minute pairs", "summed hours between first and last daily observations", sum(deployment_day_hours$hours_between_first_and_last)),
  metric("30-minute pairs", "peak unique observation hour", hour_counts_unique$hour[1], "unique observations", paste(hour_counts_unique$unique_observations[1], "observations")),
  metric("30-minute pairs", "peak paired time t hour", hour_counts_paired_t$hour[1], "paired time t rows", paste(hour_counts_paired_t$paired_time_t_rows[1], "rows")),
  metric("30-minute pairs", "16:00 unique observations", hour_counts_unique$unique_observations[hour_counts_unique$hour == "16:00"], "unique observations"),
  metric("30-minute pairs", "16:00 paired time t rows", hour_counts_paired_t$paired_time_t_rows[hour_counts_paired_t$hour == "16:00"], "paired time t rows"),
  summarise_numeric(lag_data, "max_gust", "30-minute weather", "maximum gust"),
  summarise_numeric(lag_data, "temperature_avg", "30-minute weather", "average temperature"),
  summarise_numeric(lag_data, "minutes_above_threshold", "30-minute threshold", "minutes above 2 m/s"),
  summarise_numeric(unique_obs, "total_butterflies", "30-minute butterfly index", "Butterfly Index"),
  metric(
    "30-minute direct sun",
    "observations with butterflies in direct sun",
    sum(lag_data$butterflies_direct_sun_t_lag > 0, na.rm = TRUE),
    "paired rows",
    paste0(round(mean(lag_data$butterflies_direct_sun_t_lag > 0, na.rm = TRUE) * 100, 1), "%")
  ),
  metric("30-minute direct sun", "mean butterflies in direct sun when present", mean(lag_data$butterflies_direct_sun_t_lag[lag_data$butterflies_direct_sun_t_lag > 0], na.rm = TRUE)),
  metric("30-minute direct sun", "maximum butterflies in direct sun when present", max(lag_data$butterflies_direct_sun_t_lag, na.rm = TRUE)),
  metric("Next Day Window", "filtered rows", nrow(next_day), "metrics_complete >= 0.95"),
  summarise_numeric(next_day, "max_butterflies_t_1", "Next Day Window", "previous day maximum Butterfly Index"),
  summarise_numeric(next_day, "butterfly_diff", "Next Day Window", "change in maximum Butterfly Index"),
  summarise_numeric(next_day, "wind_max_gust", "Next Day Window", "maximum wind gust"),
  summarise_numeric(next_day, "sum_butterflies_direct_sun", "Next Day Window", "cumulative butterflies in direct sun"),
  summarise_numeric(next_day, "lag_duration_hours", "Next Day Window", "window duration hours"),
  metric("24-hour robustness", "filtered rows", nrow(hr24), "metrics_complete >= 0.95"),
  summarise_numeric(hr24, "max_butterflies_t_1", "24-hour robustness", "previous day maximum Butterfly Index"),
  summarise_numeric(hr24, "butterfly_diff", "24-hour robustness", "change in maximum Butterfly Index"),
  summarise_numeric(hr24, "wind_max_gust", "24-hour robustness", "maximum wind gust"),
  summarise_numeric(hr24, "sum_butterflies_direct_sun", "24-hour robustness", "cumulative butterflies in direct sun"),
  summarise_numeric(hr24, "lag_duration_hours", "24-hour robustness", "window duration hours")
)

write_csv(metrics, file.path(out_dir, "descriptive_statistics.csv"))
write_csv(per_deployment_bi, file.path(out_dir, "per_deployment_butterfly_index.csv"))
write_csv(hour_counts_unique, file.path(out_dir, "hour_counts_unique_observations.csv"))
write_csv(hour_counts_paired_t, file.path(out_dir, "hour_counts_paired_time_t.csv"))

report <- c(
  "# Descriptive Statistics",
  "",
  paste("30-minute paired rows:", nrow(lag_data)),
  paste("Unique observation frames:", nrow(unique_obs)),
  paste("Date range:", min(unique_obs$date), "to", max(unique_obs$date)),
  paste("Peak hour among unique observations:", hour_counts_unique$hour[1], paste0("(", hour_counts_unique$unique_observations[1], " observations)")),
  paste("Peak hour among paired time t rows:", hour_counts_paired_t$hour[1], paste0("(", hour_counts_paired_t$paired_time_t_rows[1], " rows)")),
  "",
  "The paired-row and unique-observation hour counts intentionally differ. Use the paired-row count when describing analysis rows. Use the unique-observation count when describing images."
)
writeLines(report, file.path(out_dir, "descriptive_statistics.md"))

message("Wrote descriptive statistics to ", out_dir)

