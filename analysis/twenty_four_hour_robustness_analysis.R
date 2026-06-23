#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(mgcv)
  library(nlme)
  library(readr)
  library(tibble)
  library(here)
})

source(here("analysis", "lib", "plot_binned_interaction.R"))

out_dir <- here("analysis", "outputs", "24_hour")
fig_out_dir <- file.path(out_dir, "figures")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(fig_out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(here("figures"), recursive = TRUE, showWarnings = FALSE)

cfg <- list(
  dpi = 600,
  interaction_w = 7,
  interaction_h = 6,
  display_width = 6,
  target_axis_title = 12,
  target_axis_text = 10
)

save_both <- function(filename, plot, width, height) {
  ggsave(file.path(fig_out_dir, filename), plot, width = width, height = height, dpi = cfg$dpi, bg = "white")
  ggsave(here("figures", filename), plot, width = width, height = height, dpi = cfg$dpi, bg = "white")
}

data <- read_csv(here("data", "monarch_daily_lag_analysis_24hr_window.csv"), show_col_types = FALSE) %>%
  mutate(
    butterfly_diff_sqrt = sign(butterfly_diff) * sqrt(abs(butterfly_diff))
  ) %>%
  filter(metrics_complete >= 0.95) %>%
  arrange(deployment_id, observation_order_t) %>%
  mutate(
    deployment_id = factor(deployment_id),
    across(c(max_butterflies_t_1, wind_max_gust, sum_butterflies_direct_sun), as.numeric)
  ) %>%
  filter(
    !is.na(butterfly_diff_sqrt),
    !is.na(max_butterflies_t_1),
    !is.na(wind_max_gust),
    !is.na(sum_butterflies_direct_sun)
  )

model <- gamm(
  butterfly_diff_sqrt ~ s(max_butterflies_t_1, k = 5) + ti(wind_max_gust, sum_butterflies_direct_sun),
  data = data,
  random = list(deployment_id = ~1),
  correlation = corAR1(form = ~ observation_order_t | deployment_id),
  method = "REML"
)

comparison <- read_csv(file.path(out_dir, "model_comparison_24hr.csv"), show_col_types = FALSE)
top5 <- comparison %>%
  arrange(delta_AICc) %>%
  slice(1:5) %>%
  transmute(
    Model = model,
    Terms = description,
    AICc = round(AICc, 3),
    Delta_AICc = round(delta_AICc, 3),
    Weight = round(weight_AICc, 4)
  )
write_csv(top5, file.path(out_dir, "24hr_model_selection.csv"))

model_summary <- summary(model$gam)
smooths <- as.data.frame(model_summary$s.table) %>%
  rownames_to_column("term") %>%
  as_tibble()
write_csv(smooths, file.path(out_dir, "24hr_model_summary.csv"))

fit_stats <- tibble(
  model = "M31",
  n = nrow(data),
  adjusted_r_squared = model_summary$r.sq,
  scale = model_summary$scale,
  formula = "butterfly_diff_sqrt ~ s(max_butterflies_t_1, k = 5) + ti(wind_max_gust, sum_butterflies_direct_sun)"
)
write_csv(fit_stats, file.path(out_dir, "24hr_model_fit_statistics.csv"))

descriptive <- tibble(
  metric = c(
    "filtered rows",
    "previous day maximum BI mean",
    "previous day maximum BI sd",
    "change in maximum BI mean",
    "change in maximum BI sd",
    "maximum wind gust mean",
    "maximum wind gust sd",
    "cumulative butterflies in direct sun mean",
    "cumulative butterflies in direct sun sd",
    "window duration mean",
    "window duration sd"
  ),
  value = c(
    nrow(data),
    mean(data$max_butterflies_t_1),
    sd(data$max_butterflies_t_1),
    mean(data$butterfly_diff),
    sd(data$butterfly_diff),
    mean(data$wind_max_gust),
    sd(data$wind_max_gust),
    mean(data$sum_butterflies_direct_sun),
    sd(data$sum_butterflies_direct_sun),
    mean(data$lag_duration_hours),
    sd(data$lag_duration_hours)
  )
)
write_csv(descriptive, file.path(out_dir, "descriptive_statistics.csv"))

interaction_wind_sun_24hr <- create_binned_interaction_plot(
  gam_model = model$gam,
  x_var = "wind_max_gust",
  y_var = "sum_butterflies_direct_sun",
  data = data,
  xlab = "Maximum wind speed (m/s)",
  ylab = "Butterflies in direct sun",
  n = 400,
  limits = c(-16, 16),
  breaks = seq(-16, 16, by = 2),
  labels = c("-16", "-14", "-12", "-10", "-8", "-6", "-4", "-2", "0", "+2", "+4", "+6", "+8", "+10", "+12", "+14", "+16"),
  too_far = 0.04,
  barheight = 40,
  barwidth = 1.0,
  legend_text_size = round(cfg$target_axis_text * cfg$interaction_w / cfg$display_width),
  legend_key_height_cm = 2.0
) +
  theme(
    axis.title = element_text(size = round(cfg$target_axis_title * cfg$interaction_w / cfg$display_width)),
    axis.text = element_text(size = round(cfg$target_axis_text * cfg$interaction_w / cfg$display_width))
  )
save_both("interaction_wind_sun_24hr.png", interaction_wind_sun_24hr, cfg$interaction_w, cfg$interaction_h)

message("Wrote 24-hour robustness outputs to ", out_dir)
