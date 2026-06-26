#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(mgcv)
  library(nlme)
  library(patchwork)
  library(readr)
  library(tibble)
  library(here)
})

source(here("analysis", "lib", "plot_binned_interaction.R"))
source(here("analysis", "lib", "manuscript_figure_style.R"))

out_dir <- here("analysis", "outputs", "next_day_window")
fig_out_dir <- file.path(out_dir, "figures")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(fig_out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(here("figures"), recursive = TRUE, showWarnings = FALSE)

cfg <- list(
  dpi = 600,
  display_width = 6,
  target_axis_title = 12,
  target_axis_text = 10,
  interaction_w = 7,
  interaction_h = 6,
  interaction_include_width = 0.70,
  diagnostic_h = 5,
  diagnostic_include_width = 0.80,
  acf_w = 7,
  acf_h = 5,
  acf_include_width = 0.70,
  col_prev = "#9673c5",
  col_time = "#79a44c"
)

make_theme <- function(fig_width) {
  scale_factor <- fig_width / cfg$display_width
  theme_minimal(base_size = round(cfg$target_axis_title * scale_factor)) +
    theme(
      panel.grid.major = element_line(color = "gray90", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray95", linewidth = 0.3),
      axis.text = element_text(color = "black", size = round(cfg$target_axis_text * scale_factor)),
      axis.title = element_text(color = "black", size = round(cfg$target_axis_title * scale_factor)),
      plot.title = element_blank(),
      plot.subtitle = element_blank(),
      plot.caption = element_blank()
    )
}

lighten_color <- function(hex, amount = 0.12) {
  rgbv <- col2rgb(hex)
  out <- rgbv + (255 - rgbv) * amount
  rgb(out[1], out[2], out[3], maxColorValue = 255)
}

save_both <- function(filename, plot, width, height) {
  ggsave(file.path(fig_out_dir, filename), plot, width = width, height = height, dpi = cfg$dpi, bg = "white")
  ggsave(here("figures", filename), plot, width = width, height = height, dpi = cfg$dpi, bg = "white")
}

save_acf_both <- function(filename, residuals) {
  acf_cex <- acf_cex_like_reference(cfg$acf_w, cfg$acf_include_width)
  for (path in c(file.path(fig_out_dir, filename), here("figures", filename))) {
    png(path, width = cfg$acf_w, height = cfg$acf_h, units = "in", res = cfg$dpi)
    par(cex.lab = acf_cex$lab, cex.axis = acf_cex$axis, cex.main = acf_cex$lab, mar = c(5, 5, 2, 2))
    acf(residuals, main = "", xlab = "Lag", ylab = "Autocorrelation")
    dev.off()
  }
}

data <- read_csv(here("data", "monarch_daily_lag_analysis_nextday_window.csv"), show_col_types = FALSE) %>%
  mutate(
    butterfly_diff_sqrt = sign(butterfly_diff) * sqrt(abs(butterfly_diff))
  ) %>%
  filter(metrics_complete >= 0.95) %>%
  arrange(deployment_id, observation_order_t) %>%
  mutate(
    deployment_id = factor(deployment_id),
    across(
      c(max_butterflies_t_1, lag_duration_hours, wind_max_gust, sum_butterflies_direct_sun),
      as.numeric
    )
  ) %>%
  filter(
    !is.na(butterfly_diff_sqrt),
    !is.na(max_butterflies_t_1),
    !is.na(lag_duration_hours),
    !is.na(wind_max_gust),
    !is.na(sum_butterflies_direct_sun)
  )

model <- gamm(
  butterfly_diff_sqrt ~ max_butterflies_t_1 + lag_duration_hours + ti(wind_max_gust, sum_butterflies_direct_sun),
  data = data,
  random = list(deployment_id = ~1),
  correlation = corAR1(form = ~ observation_order_t | deployment_id),
  method = "REML"
)

model_table <- read_csv(file.path(out_dir, "model_comparison_comprehensive.csv"), show_col_types = FALSE)
top5 <- model_table %>%
  arrange(delta_AICc) %>%
  slice(1:5) %>%
  transmute(
    Model = model,
    Terms = description,
    AICc = round(AICc, 3),
    Delta_AICc = round(delta_AICc, 3),
    Weight = round(weight_AICc, 4)
  )
write_csv(top5, file.path(out_dir, "nextday_model_selection.csv"))

model_summary <- summary(model$gam)
parametric <- as.data.frame(model_summary$p.table) %>%
  rownames_to_column("term") %>%
  as_tibble() %>%
  mutate(term_type = "parametric")
smooths <- as.data.frame(model_summary$s.table) %>%
  rownames_to_column("term") %>%
  as_tibble() %>%
  mutate(term_type = "smooth")
write_csv(bind_rows(parametric, smooths), file.path(out_dir, "nextday_model_summary.csv"))

fit_stats <- tibble(
  model = "M32",
  n = nrow(data),
  adjusted_r_squared = model_summary$r.sq,
  scale = model_summary$scale,
  formula = "butterfly_diff_sqrt ~ max_butterflies_t_1 + lag_duration_hours + ti(wind_max_gust, sum_butterflies_direct_sun)"
)
write_csv(fit_stats, file.path(out_dir, "nextday_model_fit_statistics.csv"))

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

partial_prev <- ggplot(data, aes(max_butterflies_t_1, butterfly_diff_sqrt)) +
  geom_point(alpha = 0.4, size = 1.5, color = "#4d4d4d") +
  geom_smooth(method = "lm", se = TRUE, color = cfg$col_prev, fill = lighten_color(cfg$col_prev)) +
  labs(
    x = "Previous day maximum Butterfly Index",
    y = expression(paste("Partial effect on ", Delta, "BI"))
  ) +
  make_theme(9)

partial_duration <- ggplot(data, aes(lag_duration_hours, butterfly_diff_sqrt)) +
  geom_point(alpha = 0.4, size = 1.5, color = "#4d4d4d") +
  geom_smooth(method = "lm", se = TRUE, color = cfg$col_time, fill = lighten_color(cfg$col_time)) +
  labs(x = "Window duration (hours)", y = "") +
  make_theme(9)

partial_effects_nextday <- wrap_plots(partial_prev, partial_duration, nrow = 1)
save_both("partial_effects_nextday.png", partial_effects_nextday, 9, 5)

interaction_sizes <- reference_sizes(cfg$interaction_w, cfg$interaction_include_width)

interaction_wind_sun_nextday <- create_binned_interaction_plot(
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
  legend_text_size = interaction_sizes$legend_text,
  legend_title_size = interaction_sizes$legend_title,
  axis_title_size = interaction_sizes$axis_title,
  axis_text_size = interaction_sizes$axis_text,
  base_size = interaction_sizes$axis_title,
  legend_key_height_cm = 2.0
)
save_both("interaction_wind_sun_nextday.png", interaction_wind_sun_nextday, cfg$interaction_w, cfg$interaction_h)

residuals_df <- tibble(
  fitted = fitted(model$lme),
  resid = residuals(model$lme, type = "normalized")
)

diagnostic_theme <- theme_like_reference(9, cfg$diagnostic_include_width)

diagnostics_nextday <- wrap_plots(
  ggplot(residuals_df, aes(sample = resid)) +
    stat_qq(alpha = 0.3, size = 1, color = "#4d4d4d") +
    stat_qq_line(color = "#2c7fb8", linewidth = 0.8) +
    labs(x = "Theoretical quantiles", y = "Sample quantiles") +
    diagnostic_theme,
  ggplot(residuals_df, aes(fitted, resid)) +
    geom_point(alpha = 0.3, size = 1, color = "#4d4d4d") +
    geom_smooth(se = FALSE, color = "#2c7fb8", linewidth = 0.8, method = "loess", span = 0.8) +
    geom_hline(yintercept = 0, color = "gray65") +
    labs(x = "Fitted values", y = "Standardized residuals") +
    diagnostic_theme,
  nrow = 1
)
save_both("diagnostics_nextday.png", diagnostics_nextday, 9, cfg$diagnostic_h)

save_acf_both("acf_nextday.png", residuals_df$resid)

message("Wrote Next Day Window outputs to ", out_dir)
