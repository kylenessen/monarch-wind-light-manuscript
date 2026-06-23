#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(readr)
  library(tibble)
  library(here)
})

out_dir <- here("analysis", "outputs", "linear_regression")
fig_dir <- here("figures")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

cfg <- list(
  dpi = 600,
  scatter_w = 7,
  scatter_h = 6,
  show_threshold_line = FALSE
)

make_theme <- function() {
  theme_minimal(base_size = 14) +
    theme(
      panel.grid.major = element_line(color = "gray90", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray95", linewidth = 0.3),
      axis.text = element_text(color = "black"),
      axis.title = element_text(color = "black"),
      plot.title = element_blank(),
      plot.subtitle = element_blank(),
      plot.caption = element_blank()
    )
}

save_scatter <- function(path, data, x_var, y_var, xlab, ylab) {
  p <- ggplot(data, aes(x = .data[[x_var]], y = .data[[y_var]])) +
    geom_jitter(alpha = 0.45, size = 1.5, color = "#4d4d4d", width = 0.1, height = 0) +
    geom_smooth(method = "lm", se = TRUE, color = "steelblue", fill = "steelblue", alpha = 0.25, linewidth = 1) +
    geom_hline(yintercept = 0, color = "gray65", linewidth = 0.5) +
    labs(x = xlab, y = ylab) +
    make_theme()

  if (cfg$show_threshold_line) {
    p <- p + geom_vline(xintercept = 2, color = "red", linetype = "dashed", linewidth = 0.7)
  }

  ggsave(path, p, width = cfg$scatter_w, height = cfg$scatter_h, dpi = cfg$dpi, bg = "white")
}

lm_summary_row <- function(label, model, data, x_var, y_var) {
  sm <- summary(model)
  slope <- unname(coef(sm)[x_var, "Estimate"])
  se <- unname(coef(sm)[x_var, "Std. Error"])
  p_value <- unname(coef(sm)[x_var, "Pr(>|t|)"])
  r_value <- cor(data[[x_var]], data[[y_var]], use = "complete.obs")

  tibble(
    analysis = label,
    response = y_var,
    predictor = x_var,
    n = nrow(data),
    beta = slope,
    standard_error = se,
    p_value = p_value,
    r = r_value,
    r_squared = sm$r.squared
  )
}

label_dbi <- expression(paste("Change in Butterfly Index (", Delta, "BI)"))

lag_data <- read_csv(here("data", "monarch_analysis_lag30min.csv"), show_col_types = FALSE) %>%
  filter(!is.na(max_gust), !is.na(butterfly_difference))

next_day_raw <- read_csv(here("data", "monarch_daily_lag_analysis_nextday_window.csv"), show_col_types = FALSE)

next_day_max <- next_day_raw %>%
  filter(!is.na(wind_max_gust), !is.na(butterfly_diff))

next_day_max_filtered <- next_day_raw %>%
  filter(metrics_complete >= 0.95, !is.na(wind_max_gust), !is.na(butterfly_diff))

next_day_95th <- next_day_raw %>%
  filter(!is.na(wind_max_gust), !is.na(butterfly_diff_95th))

lm_30 <- lm(butterfly_difference ~ max_gust, data = lag_data)
lm_next_day_max <- lm(butterfly_diff ~ wind_max_gust, data = next_day_max)
lm_next_day_max_filtered <- lm(butterfly_diff ~ wind_max_gust, data = next_day_max_filtered)
lm_next_day_95th <- lm(butterfly_diff_95th ~ wind_max_gust, data = next_day_95th)

summary_rows <- bind_rows(
  lm_summary_row("30-minute manuscript figure", lm_30, lag_data, "max_gust", "butterfly_difference"),
  lm_summary_row("Next Day manuscript figure, maximum BI response", lm_next_day_max, next_day_max, "wind_max_gust", "butterfly_diff"),
  lm_summary_row("Next Day GAMM-filtered maximum BI response", lm_next_day_max_filtered, next_day_max_filtered, "wind_max_gust", "butterfly_diff"),
  lm_summary_row("Next Day historical 95th percentile response", lm_next_day_95th, next_day_95th, "wind_max_gust", "butterfly_diff_95th")
)

write_csv(summary_rows, file.path(out_dir, "linear_regression_summary.csv"))

save_scatter(
  here("figures", "wind_linear_30min.png"),
  lag_data,
  "max_gust",
  "butterfly_difference",
  "Maximum wind speed (m/s)",
  label_dbi
)

save_scatter(
  here("figures", "wind_linear_nextday.png"),
  next_day_max,
  "wind_max_gust",
  "butterfly_diff",
  "Maximum wind speed (m/s)",
  label_dbi
)

message("Wrote linear regression summary to ", out_dir)
message("Updated wind_linear_30min.png and wind_linear_nextday.png in ", fig_dir)
