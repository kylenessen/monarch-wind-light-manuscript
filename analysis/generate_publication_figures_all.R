#!/usr/bin/env Rscript
# ============================================================================
# PUBLICATION FIGURE GENERATION SCRIPT
# Generates all manuscript figures with Francis's requested formatting changes.
# Run this script to regenerate all figures in one go.
#
# Formatting per MDPI/Insects spec + Francis's requests:
#   - 600 dpi PNG output for journal submission
#   - Increased font sizes for half-page (~8.5 cm) reproduction
#   - Y-axis: "Change in Butterfly Index (ΔBI)" on scatter plots
#   - Partial effect labels: "Partial effect on ΔBI"
#   - Terminology: BI, Delta BI, and Next Day Window
#   - 2 m/s threshold dashed lines removed from wind-light interaction plots
#   - 2 m/s threshold dashed line retained in wind-at-clusters histogram
#   - File naming: semantic names matching manuscript labels
# ============================================================================

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
  library(ggplot2)
  library(mgcv)
  library(nlme)
  library(gratia)
  library(patchwork)
  library(here)
})

source(here("analysis", "lib", "manuscript_figure_style.R"))

# ============================================================================
# CONFIGURATION. Adjust these to quickly change all figures.
# ============================================================================
cfg <- list(
  # Output directory
  out_dir = here("figures"),
  threshold_fig_dir = here("analysis", "outputs", "threshold", "figures"),

  # Display width: ~0.9\textwidth on MDPI's 17.1cm page ≈ 6 inches
  # All font sizes are computed from these targets so every figure
  # renders at the same apparent size in the final PDF.
  display_width = 6,  # inches
  target_axis_title = 12,  # pt at final display size
  target_axis_text  = 10,
  target_legend_title = 11,
  target_legend_text  = 10,

  # Figure dimensions (inches)
  combined_scatter_w = 7, combined_scatter_h = 4.2,
  interaction_w = 7, interaction_h = 6,
  interaction_include_width = 0.70,
  diagnostic_h = 5,
  diagnostic_include_width = 0.80,
  acf_w = 7, acf_h = 5,
  acf_include_width = 0.70,
  wind_at_clusters_include_width = 0.75,

  # DPI

  dpi = 600,

  # Colors
  col_prev = "#9673c5",
  col_time = "#79a44c",
  col_temp = "#b86e7e",

  # Show 2 m/s threshold line on wind-light interaction plots?
  show_threshold_line = FALSE,

  # Interaction plot settings
  interaction_n = 400,
  interaction_too_far = 0.04,
  interaction_limits = c(-6, 6),
  interaction_breaks = c(-6, -5, -4, -3, -2, -1, -0.5, 0, 0.5, 1, 2, 3, 4, 5, 6),
  interaction_labels = c("\u22126", "\u22125", "\u22124", "\u22123", "\u22122", "\u22121", "\u22120.5", "0",
                         "+0.5", "+1", "+2", "+3", "+4", "+5", "+6")
)

# Create output directories
if (!dir.exists(cfg$out_dir)) dir.create(cfg$out_dir, recursive = TRUE)
if (!dir.exists(cfg$threshold_fig_dir)) dir.create(cfg$threshold_fig_dir, recursive = TRUE)

# ============================================================================
# SHARED THEME. Scales font sizes so all figures render identically in LaTeX.
# ============================================================================
make_pub_theme <- function(fig_width) {
  s <- fig_width / cfg$display_width
  theme_minimal(base_size = round(cfg$target_axis_title * s)) +
    theme(
      panel.grid.major = element_line(color = "gray90", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray95", linewidth = 0.3),
      axis.text = element_text(color = "black", size = round(cfg$target_axis_text * s)),
      axis.title = element_text(color = "black", size = round(cfg$target_axis_title * s)),
      plot.title = element_blank(),
      plot.subtitle = element_blank(),
      plot.caption = element_blank(),
      legend.title = element_text(size = round(cfg$target_legend_title * s)),
      legend.text = element_text(size = round(cfg$target_legend_text * s)),
      strip.text = element_text(size = round(cfg$target_legend_title * s))
    )
}

# Convenience: compute base R cex values for ACF plots
make_acf_cex <- function(fig_width) {
  s <- fig_width / cfg$display_width
  list(
    lab  = cfg$target_axis_title * s / 12,  # 12pt = cex 1.0
    axis = cfg$target_axis_text * s / 12
  )
}

lighten_color <- function(hex, amount = 0.12) {
  rgbv <- col2rgb(hex)
  out <- rgbv + (255 - rgbv) * amount
  rgb(out[1], out[2], out[3], maxColorValue = 255)
}

save_fig <- function(filename, plot, w, h) {
  path <- file.path(cfg$out_dir, filename)
  ggsave(path, plot, width = w, height = h, dpi = cfg$dpi, bg = "white")
  cat(sprintf("  Saved: %s\n", filename))
}

# ============================================================================
# LOAD DATA
# ============================================================================
cat("Loading data...\n")
monarch_data <- read_csv(here("data", "monarch_analysis_lag30min.csv"),
                         show_col_types = FALSE)

model_data <- monarch_data %>%
  filter(
    !is.na(butterfly_difference_cbrt),
    !is.na(total_butterflies_t_lag),
    !is.na(max_gust),
    !is.na(temperature_avg),
    !is.na(butterflies_direct_sun_t_lag),
    !is.na(deployment_id),
    !is.na(deployment_day),
    !is.na(Observer),
    !is.na(observation_order_within_day_t)
  )

cat(sprintf("  30-min data: %d observations\n", nrow(model_data)))

# ============================================================================
# FIT KEY MODELS
# ============================================================================
cat("\nFitting models...\n")

random_30min <- list(deployment_id = ~1, Observer = ~1, deployment_day = ~1)
cor_30min <- corAR1(form = ~ observation_order_within_day_t | deployment_day)

fit_gamm <- function(formula_str, data, random, correlation) {
  gamm(as.formula(formula_str), data = data,
       random = random, correlation = correlation, method = "REML")
}

# 30-min best model (M50)
cat("  Fitting M50 (30-min best)...")
M50 <- fit_gamm(
  "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + s(temperature_avg) + s(time_within_day_t) + ti(max_gust, butterflies_direct_sun_t_lag)",
  model_data, random_30min, cor_30min)
cat(" done\n")

# 30-min threshold model (T50)
cat("  Fitting T50 (threshold best)...")
T50 <- fit_gamm(
  "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + s(temperature_avg) + s(time_within_day_t) + ti(minutes_above_threshold, butterflies_direct_sun_t_lag)",
  model_data, random_30min, cor_30min)
cat(" done\n")

# Next Day Window
nextday_data <- read_csv(here("data", "monarch_daily_lag_analysis_nextday_window.csv"),
                         show_col_types = FALSE) %>%
  mutate(butterfly_diff_sqrt = sign(butterfly_diff) * sqrt(abs(butterfly_diff))) %>%
  filter(metrics_complete >= 0.95) %>%
  arrange(deployment_id, observation_order_t) %>%
  mutate(deployment_id = factor(deployment_id),
         across(c(max_butterflies_t_1, lag_duration_hours,
                  temp_min, temp_max, temp_at_max_count_t_1,
                  wind_max_gust, sum_butterflies_direct_sun), as.numeric)) %>%
  filter(!is.na(butterfly_diff_sqrt), !is.na(max_butterflies_t_1), !is.na(lag_duration_hours))

cat(sprintf("  Next Day Window data: %d observations\n", nrow(nextday_data)))

random_daily <- list(deployment_id = ~1)
cor_daily <- corAR1(form = ~ observation_order_t | deployment_id)

cat("  Fitting M32 (Next Day Window best)...")
M32_nextday <- fit_gamm(
  "butterfly_diff_sqrt ~ max_butterflies_t_1 + lag_duration_hours + ti(wind_max_gust, sum_butterflies_direct_sun)",
  nextday_data, random_daily, cor_daily)
cat(" done\n")

# 24-hour window
hr24_data <- read_csv(here("data", "monarch_daily_lag_analysis_24hr_window.csv"),
                      show_col_types = FALSE) %>%
  mutate(butterfly_diff_sqrt = sign(butterfly_diff) * sqrt(abs(butterfly_diff))) %>%
  filter(metrics_complete >= 0.95) %>%
  arrange(deployment_id, observation_order_t) %>%
  mutate(deployment_id = factor(deployment_id),
         across(c(max_butterflies_t_1,
                  temp_min, temp_max, temp_at_max_count_t_1,
                  wind_max_gust, sum_butterflies_direct_sun), as.numeric)) %>%
  filter(!is.na(butterfly_diff_sqrt), !is.na(max_butterflies_t_1))

cat(sprintf("  24hr data: %d observations\n", nrow(hr24_data)))

cat("  Fitting M31 (24hr best)...")
M31_24hr <- fit_gamm(
  "butterfly_diff_sqrt ~ s(max_butterflies_t_1, k = 5) + ti(wind_max_gust, sum_butterflies_direct_sun)",
  hr24_data, random_daily,
  corAR1(form = ~ observation_order_t | deployment_id))
cat(" done\n")

cat("\nAll models fitted.\n\n")

# ============================================================================
# Wind linear scatter, 30-minute window
# ============================================================================
cat("Generating figures...\n")

lm_30 <- lm(butterfly_difference ~ max_gust, data = model_data)
lm_30_s <- summary(lm_30)
r_30 <- cor(model_data$max_gust, model_data$butterfly_difference)

p_main <- ggplot(model_data, aes(x = max_gust, y = butterfly_difference)) +
  geom_jitter(alpha = 0.4, size = 1.5, color = "#4d4d4d", width = 0.1, height = 0) +
  geom_smooth(method = "lm", se = TRUE, color = "steelblue", fill = "steelblue",
              alpha = 0.25, linewidth = 1) +
  geom_hline(yintercept = 0, color = "gray65", linewidth = 0.5) +
  labs(x = "Maximum wind speed (m/s)",
       y = expression(paste("Change in Butterfly Index (", Delta, "BI)"))) +
  make_pub_theme(cfg$combined_scatter_w)

if (cfg$show_threshold_line) {
  p_main <- p_main +
    geom_vline(xintercept = 2, color = "red", linetype = "dashed", linewidth = 0.7)
}

# ============================================================================
# Wind linear scatter, Next Day Window, untransformed, using max BI change
# ============================================================================
# Use unfiltered data for linear regression (n=101)
nextday_lm_data <- read_csv(here("data", "monarch_daily_lag_analysis_nextday_window.csv"),
                            show_col_types = FALSE) %>%
  filter(!is.na(wind_max_gust), !is.na(butterfly_diff))

lm_nextday <- lm(butterfly_diff ~ wind_max_gust, data = nextday_lm_data)

p_nextday_scatter <- ggplot(nextday_lm_data, aes(x = wind_max_gust, y = butterfly_diff)) +
  geom_jitter(alpha = 0.5, size = 2, color = "#4d4d4d", width = 0.1, height = 0) +
  geom_smooth(method = "lm", se = TRUE, color = "steelblue", fill = "steelblue",
              alpha = 0.25, linewidth = 1) +
  geom_hline(yintercept = 0, color = "gray65", linewidth = 0.5) +
  labs(x = "Maximum wind speed (m/s)",
       y = expression(paste("Change in Butterfly Index (", Delta, "BI)"))) +
  make_pub_theme(cfg$combined_scatter_w)

if (cfg$show_threshold_line) {
  p_nextday_scatter <- p_nextday_scatter +
    geom_vline(xintercept = 2, color = "red", linetype = "dashed", linewidth = 0.7)
}

wind_linear_x_limits <- range(c(model_data$max_gust, nextday_lm_data$wind_max_gust), na.rm = TRUE)
wind_linear_x_limits <- c(0, ceiling(wind_linear_x_limits[2]))
wind_linear_y_limits <- range(c(model_data$butterfly_difference, nextday_lm_data$butterfly_diff), na.rm = TRUE)
wind_linear_y_limits <- range(pretty(wind_linear_y_limits, n = 5))

wind_panel_title_theme <- theme(
  plot.title = element_text(
    color = "black",
    size = round(cfg$target_axis_title * cfg$combined_scatter_w / cfg$display_width),
    face = "plain",
    hjust = 0.5,
    margin = margin(b = 4)
  )
)

p_main_combined <- p_main +
  labs(title = "A. 30-minute window") +
  coord_cartesian(xlim = wind_linear_x_limits, ylim = wind_linear_y_limits) +
  wind_panel_title_theme

p_nextday_combined <- p_nextday_scatter +
  labs(title = "B. Next Day Window", y = NULL) +
  coord_cartesian(xlim = wind_linear_x_limits, ylim = wind_linear_y_limits) +
  wind_panel_title_theme

save_fig(
  "wind_linear_combined.png",
  p_main_combined + p_nextday_combined + plot_layout(ncol = 2),
  cfg$combined_scatter_w,
  cfg$combined_scatter_h
)

# ============================================================================
# Wind-at-clusters histogram
# ============================================================================
cluster_wind_data <- monarch_data %>%
  filter(!is.na(max_gust), !is.na(total_butterflies_t), total_butterflies_t > 0)

wind_at_clusters_histogram <- ggplot(cluster_wind_data, aes(x = max_gust)) +
  geom_histogram(
    binwidth = 0.25,
    boundary = 0,
    fill = "steelblue",
    color = "white",
    linewidth = 0.25
  ) +
  geom_vline(xintercept = 2, color = "#c23b3b", linetype = "dashed", linewidth = 0.8) +
  annotate(
    "text",
    x = 2.15,
    y = Inf,
    label = "2 m/s",
    hjust = 0,
    vjust = 1.3,
    color = "#c23b3b",
    size = ggplot_text_size(reference_text_size(reference_figure_style$axis_text, 6.5, cfg$wind_at_clusters_include_width))
  ) +
  scale_x_continuous(
    limits = c(0, ceiling(max(cluster_wind_data$max_gust, na.rm = TRUE))),
    breaks = seq(0, ceiling(max(cluster_wind_data$max_gust, na.rm = TRUE)), by = 2),
    expand = expansion(mult = c(0, 0.02))
  ) +
  labs(x = "Maximum wind gust speed (m/s)", y = "Frequency") +
  theme_like_reference(6.5, cfg$wind_at_clusters_include_width, grid_minor = FALSE) +
  theme(panel.grid.minor = element_blank())

save_fig("wind_at_clusters_histogram.png", wind_at_clusters_histogram, 6.5, 4.0)

# ============================================================================
# Partial effects, 30-minute M50, 1x3 panel
# ============================================================================
sm <- summary(M50$gam)$s.table

# Draw individual smooth terms with gratia
p_prev_raw <- draw(M50$gam, select = "s(total_butterflies_t_lag)", rug = FALSE, residuals = FALSE)
p_time_raw <- draw(M50$gam, select = "s(time_within_day_t)", rug = FALSE, residuals = FALSE)
p_temp_raw <- draw(M50$gam, select = "s(temperature_avg)", rug = FALSE, residuals = FALSE)

# Get common y-axis limits
get_y_range <- function(p) {
  build <- ggplot_build(p)
  c(min(build$data[[1]]$ymin, na.rm = TRUE), max(build$data[[1]]$ymax, na.rm = TRUE))
}
y_ranges <- lapply(list(p_prev_raw, p_time_raw, p_temp_raw), get_y_range)
y_min <- min(sapply(y_ranges, "[", 1)) * 1.1
y_max <- max(sapply(y_ranges, "[", 2)) * 1.1

# Style each panel
style_partial <- function(p, xlab, ylab, col, col_light) {
  p <- p +
    labs(x = xlab, y = ylab) +
    make_pub_theme(12) +
    theme(plot.margin = margin(5, 15, 5, 5)) +
    coord_cartesian(ylim = c(y_min, y_max))
  for (i in seq_along(p$layers)) {
    if ("colour" %in% names(p$layers[[i]]$aes_params)) p$layers[[i]]$aes_params$colour <- col
    if ("fill" %in% names(p$layers[[i]]$aes_params)) p$layers[[i]]$aes_params$fill <- col_light
  }
  p
}

p_prev <- style_partial(p_prev_raw, "Previous butterfly count",
                         expression(paste("Partial effect on ", Delta, "BI")),
                         cfg$col_prev, lighten_color(cfg$col_prev))
p_time <- style_partial(p_time_raw, "Minutes since sunrise",
                         "",
                         cfg$col_time, lighten_color(cfg$col_time))
p_temp <- style_partial(p_temp_raw, expression(paste("Temperature (", degree, "C)")),
                         "",
                         cfg$col_temp, lighten_color(cfg$col_temp))

# Add flight threshold band to temperature panel
fade_width <- 0.5
p_temp <- p_temp +
  annotate("rect", xmin = 12.7 + fade_width, xmax = 16 - fade_width,
           ymin = -Inf, ymax = Inf, fill = "#ADD8E6", alpha = 0.35)
for (i in 1:5) {
  alpha_val <- 0.35 * (5 - i + 1) / 5
  fade_off <- fade_width * i / 5
  p_temp <- p_temp +
    annotate("rect",
             xmin = 12.7 + fade_width - fade_off,
             xmax = 12.7 + fade_width - fade_off + fade_width / 5,
             ymin = -Inf, ymax = Inf, fill = "#ADD8E6", alpha = alpha_val) +
    annotate("rect",
             xmin = 16 - fade_width + fade_off - fade_width / 5,
             xmax = 16 - fade_width + fade_off,
             ymin = -Inf, ymax = Inf, fill = "#ADD8E6", alpha = alpha_val)
}

partial_effects_30min <- wrap_plots(p_prev, p_time, p_temp, nrow = 1)
save_fig("partial_effects_30min.png", partial_effects_30min, 12, 6)

# ============================================================================
# Interaction heatmap, 30-minute M50, wind x sun
# ============================================================================
source(here("analysis", "lib", "plot_binned_interaction.R"))

interaction_sizes <- reference_sizes(cfg$interaction_w, cfg$interaction_include_width)

interaction_wind_sun_30min <- create_binned_interaction_plot(
  gam_model = M50$gam,
  x_var = "max_gust",
  y_var = "butterflies_direct_sun_t_lag",
  data = model_data,
  xlab = "Maximum wind speed (m/s)",
  ylab = "Butterflies in direct sun",
  n = cfg$interaction_n,
  limits = cfg$interaction_limits,
  breaks = c(-6, -4, -2, 0, 2, 4, 6),
  labels = c("-6", "-4", "-2", "0", "+2", "+4", "+6"),
  too_far = cfg$interaction_too_far,
  barheight = 40, barwidth = 1.0,
  legend_text_size = interaction_sizes$legend_text,
  legend_title_size = interaction_sizes$legend_title,
  axis_title_size = interaction_sizes$axis_title,
  axis_text_size = interaction_sizes$axis_text,
  base_size = interaction_sizes$axis_title,
  legend_key_height_cm = 2.0
)

if (cfg$show_threshold_line) {
  interaction_wind_sun_30min <- interaction_wind_sun_30min +
    geom_vline(xintercept = 2, color = "red", linetype = "dashed", linewidth = 0.7)
}

save_fig("interaction_wind_sun_30min.png", interaction_wind_sun_30min, cfg$interaction_w, cfg$interaction_h)

# ============================================================================
# Diagnostics, Q-Q and residuals, 30-minute M50
# ============================================================================
res_30 <- tibble(
  fitted = fitted(M50$lme),
  resid  = residuals(M50$lme, type = "normalized")
)

diag_qq <- ggplot(res_30, aes(sample = resid)) +
  stat_qq(alpha = 0.25, size = 0.8, color = "#4d4d4d") +
  stat_qq_line(color = "#2c7fb8", linewidth = 0.8) +
  labs(x = "Theoretical quantiles", y = "Sample quantiles") +
  theme_like_reference(9, cfg$diagnostic_include_width)

diag_resid <- ggplot(res_30, aes(fitted, resid)) +
  geom_point(alpha = 0.25, size = 0.8, color = "#4d4d4d") +
  geom_smooth(se = FALSE, color = "#2c7fb8", linewidth = 0.8, method = "loess", span = 0.8) +
  geom_hline(yintercept = 0, color = "gray65") +
  labs(x = "Fitted values", y = "Standardized residuals") +
  theme_like_reference(9, cfg$diagnostic_include_width)

diagnostics_30min <- wrap_plots(diag_qq, diag_resid, nrow = 1)
save_fig("diagnostics_30min.png", diagnostics_30min, 9, cfg$diagnostic_h)

# ============================================================================
# ACF, 30-minute M50
# ============================================================================
acf_cex <- acf_cex_like_reference(cfg$acf_w, cfg$acf_include_width)
png(file.path(cfg$out_dir, "acf_30min.png"),
    width = cfg$acf_w, height = cfg$acf_h, units = "in", res = cfg$dpi)
par(cex.lab = acf_cex$lab, cex.axis = acf_cex$axis, cex.main = acf_cex$lab, mar = c(5, 5, 2, 2))
acf(res_30$resid, main = "", xlab = "Lag", ylab = "Autocorrelation")
dev.off()
cat("  Saved: acf_30min.png\n")

# ============================================================================
# Threshold interaction heatmap, 30-minute T50
# ============================================================================
threshold_interaction_wind_sun <- create_binned_interaction_plot(
  gam_model = T50$gam,
  x_var = "minutes_above_threshold",
  y_var = "butterflies_direct_sun_t_lag",
  data = model_data,
  xlab = "Minutes above 2 m/s threshold",
  ylab = "Butterflies in direct sun",
  n = cfg$interaction_n,
  limits = cfg$interaction_limits,
  breaks = cfg$interaction_breaks,
  labels = cfg$interaction_labels,
  too_far = cfg$interaction_too_far,
  barheight = 40, barwidth = 1.0,
  legend_text_size = round(cfg$target_legend_text * cfg$interaction_w / cfg$display_width),
  legend_key_height_cm = 2.0
) +
  theme(axis.title = element_text(size = round(cfg$target_axis_title * cfg$interaction_w / cfg$display_width)),
        axis.text = element_text(size = round(cfg$target_axis_text * cfg$interaction_w / cfg$display_width)))

ggsave(file.path(cfg$threshold_fig_dir, "threshold_interaction_wind_sun.png"),
       threshold_interaction_wind_sun,
       width = cfg$interaction_w, height = cfg$interaction_h, dpi = cfg$dpi, bg = "white")
cat("  Saved: analysis/outputs/threshold/figures/threshold_interaction_wind_sun.png\n")

# ============================================================================
# Partial effects, Next Day Window M32, previous BI and window duration
# ============================================================================
p_nextday_prev <- ggplot(nextday_data, aes(x = max_butterflies_t_1,
                                           y = butterfly_diff_sqrt)) +
  geom_point(alpha = 0.4, size = 1.5, color = "#4d4d4d") +
  geom_smooth(method = "lm", se = TRUE, color = cfg$col_prev, fill = lighten_color(cfg$col_prev)) +
  labs(x = "Previous day maximum Butterfly Index",
       y = expression(paste("Partial effect on ", Delta, "BI"))) +
  make_pub_theme(9)

# For window duration, use the model's linear coefficient
p_nextday_dur <- ggplot(nextday_data, aes(x = lag_duration_hours,
                                          y = butterfly_diff_sqrt)) +
  geom_point(alpha = 0.4, size = 1.5, color = "#4d4d4d") +
  geom_smooth(method = "lm", se = TRUE, color = cfg$col_time, fill = lighten_color(cfg$col_time)) +
  labs(x = "Window duration (hours)",
       y = "") +
  make_pub_theme(9)

partial_effects_nextday <- wrap_plots(p_nextday_prev, p_nextday_dur, nrow = 1)
save_fig("partial_effects_nextday.png", partial_effects_nextday, 9, 5)

# ============================================================================
# Interaction heatmap, Next Day Window M32, wind x sun
# ============================================================================
interaction_wind_sun_nextday <- create_binned_interaction_plot(
  gam_model = M32_nextday$gam,
  x_var = "wind_max_gust",
  y_var = "sum_butterflies_direct_sun",
  data = nextday_data,
  xlab = "Maximum wind speed (m/s)",
  ylab = "Butterflies in direct sun",
  n = cfg$interaction_n,
  limits = c(-16, 16),
  breaks = seq(-16, 16, by = 2),
  labels = c("\u221216", "\u221214", "\u221212", "\u221210", "\u22128", "\u22126", "\u22124", "\u22122",
             "0", "+2", "+4", "+6", "+8", "+10", "+12", "+14", "+16"),
  too_far = cfg$interaction_too_far,
  barheight = 40, barwidth = 1.0,
  legend_text_size = interaction_sizes$legend_text,
  legend_title_size = interaction_sizes$legend_title,
  axis_title_size = interaction_sizes$axis_title,
  axis_text_size = interaction_sizes$axis_text,
  base_size = interaction_sizes$axis_title,
  legend_key_height_cm = 2.0
)

save_fig("interaction_wind_sun_nextday.png", interaction_wind_sun_nextday, cfg$interaction_w, cfg$interaction_h)

# ============================================================================
# Diagnostics, Q-Q and residuals, Next Day Window M32
# ============================================================================
res_nextday <- tibble(
  fitted = fitted(M32_nextday$lme),
  resid  = residuals(M32_nextday$lme, type = "normalized")
)

diagnostics_nextday <- wrap_plots(
  ggplot(res_nextday, aes(sample = resid)) +
    stat_qq(alpha = 0.3, size = 1, color = "#4d4d4d") +
    stat_qq_line(color = "#2c7fb8", linewidth = 0.8) +
    labs(x = "Theoretical quantiles", y = "Sample quantiles") + theme_like_reference(9, cfg$diagnostic_include_width),
  ggplot(res_nextday, aes(fitted, resid)) +
    geom_point(alpha = 0.3, size = 1, color = "#4d4d4d") +
    geom_smooth(se = FALSE, color = "#2c7fb8", linewidth = 0.8, method = "loess", span = 0.8) +
    geom_hline(yintercept = 0, color = "gray65") +
    labs(x = "Fitted values", y = "Standardized residuals") + theme_like_reference(9, cfg$diagnostic_include_width),
  nrow = 1
)
save_fig("diagnostics_nextday.png", diagnostics_nextday, 9, cfg$diagnostic_h)

# ============================================================================
# ACF, Next Day Window M32
# ============================================================================
png(file.path(cfg$out_dir, "acf_nextday.png"),
    width = cfg$acf_w, height = cfg$acf_h, units = "in", res = cfg$dpi)
par(cex.lab = acf_cex$lab, cex.axis = acf_cex$axis, cex.main = acf_cex$lab, mar = c(5, 5, 2, 2))
acf(res_nextday$resid, main = "", xlab = "Lag", ylab = "Autocorrelation")
dev.off()
cat("  Saved: acf_nextday.png\n")

# ============================================================================
# Interaction heatmap, 24-hour M31, wind x sun
# ============================================================================
interaction_wind_sun_24hr <- create_binned_interaction_plot(
  gam_model = M31_24hr$gam,
  x_var = "wind_max_gust",
  y_var = "sum_butterflies_direct_sun",
  data = hr24_data,
  xlab = "Maximum wind speed (m/s)",
  ylab = "Butterflies in direct sun",
  n = cfg$interaction_n,
  limits = c(-16, 16),
  breaks = seq(-16, 16, by = 2),
  labels = c("\u221216", "\u221214", "\u221212", "\u221210", "\u22128", "\u22126", "\u22124", "\u22122",
             "0", "+2", "+4", "+6", "+8", "+10", "+12", "+14", "+16"),
  too_far = cfg$interaction_too_far,
  barheight = 40, barwidth = 1.0,
  legend_text_size = interaction_sizes$legend_text,
  legend_title_size = interaction_sizes$legend_title,
  axis_title_size = interaction_sizes$axis_title,
  axis_text_size = interaction_sizes$axis_text,
  base_size = interaction_sizes$axis_title,
  legend_key_height_cm = 2.0
)

save_fig("interaction_wind_sun_24hr.png", interaction_wind_sun_24hr, cfg$interaction_w, cfg$interaction_h)

# ============================================================================
# DONE
# ============================================================================
cat(sprintf("\nAll figures saved to: %s\n", cfg$out_dir))
cat("Figures generated:\n")
cat("  wind_linear_combined.png. Two-panel linear regression scatter\n")
cat("  partial_effects_30min.png. Partial effects 1x3 (M50)\n")
cat("  interaction_wind_sun_30min.png. Wind x sun heatmap (M50)\n")
cat("  diagnostics_30min.png. Q-Q and residuals (M50)\n")
cat("  acf_30min.png. ACF (M50)\n")
cat("  partial_effects_nextday.png. Partial effects 1x2 (M32)\n")
cat("  interaction_wind_sun_nextday.png. Wind x sun heatmap (M32 Next Day)\n")
cat("  diagnostics_nextday.png. Q-Q and residuals (M32)\n")
cat("  acf_nextday.png. ACF (M32)\n")
cat("  interaction_wind_sun_24hr.png. Wind x sun heatmap (M31 24hr)\n")
cat("  analysis/outputs/threshold/figures/threshold_interaction_wind_sun.png. Threshold provenance heatmap (T50)\n")
