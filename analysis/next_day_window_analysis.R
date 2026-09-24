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

cfg <- list(
  dpi = 600,
  interaction_w = 7,
  interaction_h = 6,
  interaction_include_width = 0.72,
  diagnostic_h = 5,
  diagnostic_include_width = 0.80,
  acf_w = 7,
  acf_h = 5,
  acf_include_width = 0.70
)

save_figure <- function(filename, plot, width, height) {
  ggsave(file.path(fig_out_dir, filename), plot, width = width, height = height, dpi = cfg$dpi, bg = "white")
}

save_acf <- function(filename, residuals) {
  acf_cex <- acf_cex_like_reference(cfg$acf_w, cfg$acf_include_width)
  path <- file.path(fig_out_dir, filename)
  png(path, width = cfg$acf_w, height = cfg$acf_h, units = "in", res = cfg$dpi)
  par(cex.lab = acf_cex$lab, cex.axis = acf_cex$axis, cex.main = acf_cex$lab, mar = c(5, 5, 2, 2))
  acf(residuals, main = "", xlab = "Lag", ylab = "Autocorrelation")
  dev.off()
}

data <- read_csv(here("data", "analysis_inputs", "analysis_next_day.csv"), show_col_types = FALSE) %>%
  mutate(
    delta_bi_signed_square_root = sign(delta_bi) * sqrt(abs(delta_bi))
  ) %>%
  arrange(deployment_id, observation_order) %>%
  mutate(
    deployment_id = factor(deployment_id),
    across(
      c(previous_day_maximum_bi, window_duration_hours, maximum_wind_gust_m_s, cumulative_sun_exposed_bi),
      as.numeric
    )
  ) %>%
  filter(
    !is.na(delta_bi_signed_square_root),
    !is.na(previous_day_maximum_bi),
    !is.na(window_duration_hours),
    !is.na(maximum_wind_gust_m_s),
    !is.na(cumulative_sun_exposed_bi)
  )

# Use the primary selection from the manuscript's shared candidate framework.
selection <- read_csv(
  here("analysis", "outputs", "harmonized_model_comparison", "selected_models.csv"),
  show_col_types = FALSE
) %>%
  filter(window == "next_day", framework == "primary_previous_bi")
stopifnot(nrow(selection) == 1L, nrow(data) == selection$n[[1]])
selected_id <- selection$candidate_id[[1]]
selected_formula <- selection$formula[[1]]
model <- withCallingHandlers(
  gamm(
    as.formula(selected_formula), data = data,
    random = list(deployment_id = ~1),
    correlation = corAR1(form = ~ observation_order | deployment_id),
    method = "REML"
  ),
  warning = function(w) {
    if (grepl("convergence", conditionMessage(w), ignore.case = TRUE)) {
      stop("Selected Next Day model did not converge. ", conditionMessage(w))
    }
  }
)

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
  model = selected_id,
  n = nrow(data),
  adjusted_r_squared = model_summary$r.sq,
  scale = model_summary$scale,
  formula = selected_formula
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
    mean(data$previous_day_maximum_bi),
    sd(data$previous_day_maximum_bi),
    mean(data$delta_bi),
    sd(data$delta_bi),
    mean(data$maximum_wind_gust_m_s),
    sd(data$maximum_wind_gust_m_s),
    mean(data$cumulative_sun_exposed_bi),
    sd(data$cumulative_sun_exposed_bi),
    mean(data$window_duration_hours),
    sd(data$window_duration_hours)
  )
)
write_csv(descriptive, file.path(out_dir, "descriptive_statistics.csv"))

interaction_sizes <- reference_sizes(
  cfg$interaction_w, cfg$interaction_include_width, manuscript_figure_style
)

interaction_wind_sun_nextday <- create_binned_interaction_plot(
  gam_model = model$gam,
  x_var = "maximum_wind_gust_m_s",
  y_var = "cumulative_sun_exposed_bi",
  data = data,
  xlab = "Maximum wind gust (m/s)",
  ylab = "Cumulative sun-exposed BI",
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
  base_family = manuscript_figure_style$font_family,
  legend_key_height_cm = 2.0
)
save_figure("interaction_wind_sun_nextday.png", interaction_wind_sun_nextday, cfg$interaction_w, cfg$interaction_h)

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
save_figure("diagnostics_nextday.png", diagnostics_nextday, 9, cfg$diagnostic_h)

save_acf("acf_nextday.png", residuals_df$resid)

message("Wrote Next Day Window outputs to ", out_dir)
