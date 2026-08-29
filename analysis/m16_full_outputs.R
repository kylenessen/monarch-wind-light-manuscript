#!/usr/bin/env Rscript

# Complete statistical and graphical export for the selected 30-minute M16 model.

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(here)
  library(mgcv)
  library(nlme)
  library(patchwork)
  library(readr)
  library(tibble)
})

source(here("analysis", "lib", "manuscript_figure_style.R"))

out_dir <- here("analysis", "outputs", "30_minute", "m16")
table_dir <- file.path(out_dir, "tables")
text_dir <- file.path(out_dir, "text")
figure_dir <- file.path(out_dir, "figures")
candidate_figure_dir <- file.path(figure_dir, "candidates")
for (path in c(out_dir, table_dir, text_dir, figure_dir, candidate_figure_dir)) {
  dir.create(path, recursive = TRUE, showWarnings = FALSE)
}

model_formula <- butterfly_difference_cbrt ~
  total_butterflies_t_lag +
  max_gust * temperature_avg * butterflies_direct_sun_t_lag

required_columns <- c(
  "butterfly_difference_cbrt", "total_butterflies_t_lag",
  "temperature_avg", "max_gust", "butterflies_direct_sun_t_lag",
  "observation_order_within_day_t", "deployment_day", "deployment_id"
)

data <- read_csv(
  here("data", "monarch_analysis_lag30min.csv"),
  show_col_types = FALSE
) %>%
  filter(if_all(all_of(required_columns), ~ !is.na(.x)))

stopifnot(nrow(data) == 1894)

random_structure <- list(
  deployment_id = ~1,
  deployment_day = ~1
)
correlation_structure <- corAR1(
  form = ~ observation_order_within_day_t | deployment_day
)

fit_m16 <- function(method) {
  warnings <- character()
  fit <- withCallingHandlers(
    gamm(
      model_formula,
      data = data,
      random = random_structure,
      correlation = correlation_structure,
      method = method
    ),
    warning = function(w) {
      warnings <<- c(warnings, conditionMessage(w))
      invokeRestart("muffleWarning")
    }
  )
  if (any(grepl("convergence", warnings, ignore.case = TRUE))) {
    stop("M16 produced a convergence warning under ", method, ".")
  }
  list(fit = fit, warnings = unique(warnings))
}

ml_result <- fit_m16("ML")
reml_result <- fit_m16("REML")
model_ml <- ml_result$fit
model <- reml_result$fit
gam_summary <- summary(model$gam)
lme_summary <- summary(model$lme)

# Fixed effects and confidence intervals
lme_coefficients <- as.data.frame(lme_summary$tTable) %>%
  rownames_to_column("term") %>%
  as_tibble() %>%
  rename(
    estimate = Value,
    standard_error = Std.Error,
    denominator_df = DF,
    t_value = `t-value`,
    p_value = `p-value`
  ) %>%
  mutate(term = sub("^X", "", term))

fixed_intervals <- as.data.frame(intervals(model$lme, which = "fixed")$fixed) %>%
  rownames_to_column("term") %>%
  as_tibble() %>%
  rename(conf_low = lower, estimate_check = `est.`, conf_high = upper) %>%
  mutate(term = sub("^X", "", term))

coefficient_table <- lme_coefficients %>%
  left_join(fixed_intervals, by = "term") %>%
  select(
    term, estimate, standard_error, denominator_df, t_value, p_value,
    conf_low, conf_high
  )
write_csv(coefficient_table, file.path(table_dir, "m16_fixed_effects.csv"))

# Variance components
variance_matrix <- as.matrix(VarCorr(model$lme))
variance_rows <- list()
current_group <- NA_character_
for (i in seq_len(nrow(variance_matrix))) {
  row_label <- rownames(variance_matrix)[i]
  if (grepl(" =$", row_label)) {
    current_group <- sub(" =$", "", row_label)
    next
  }
  variance_value <- suppressWarnings(as.numeric(variance_matrix[i, "Variance"]))
  sd_value <- suppressWarnings(as.numeric(variance_matrix[i, "StdDev"]))
  if (is.finite(variance_value) && is.finite(sd_value)) {
    component <- if (row_label == "Residual") "Residual" else current_group
    variance_rows[[length(variance_rows) + 1]] <- tibble(
      component = component,
      term = row_label,
      variance = variance_value,
      standard_deviation = sd_value
    )
  }
}
variance_table <- bind_rows(variance_rows)
write_csv(variance_table, file.path(table_dir, "m16_variance_components.csv"))

# Fit statistics
ml_loglik <- logLik(model_ml$lme)
reml_loglik <- logLik(model$lme)
model_audit <- read_csv(
  here("analysis", "outputs", "30_minute", "model_audit_30min.csv"),
  show_col_types = FALSE
)
m16_audit <- model_audit %>% filter(Model == "M16")
overall_test <- anova(model$lme, type = "marginal")

fit_statistics <- tibble(
  model_id = "M16",
  n = nrow(data),
  deployments = n_distinct(data$deployment_id),
  observers = n_distinct(data$Observer),
  deployment_days = n_distinct(data$deployment_day),
  adjusted_r_squared = gam_summary$r.sq,
  scale_estimate = gam_summary$scale,
  residual_standard_deviation = sqrt(gam_summary$scale),
  ml_log_likelihood = as.numeric(ml_loglik),
  ml_likelihood_df = attr(ml_loglik, "df"),
  ml_aic = AIC(model_ml$lme),
  ml_bic = BIC(model_ml$lme),
  ml_delta_aic = m16_audit$Delta_AIC,
  ml_akaike_weight = m16_audit$Weight,
  reml_log_likelihood = as.numeric(reml_loglik),
  reml_likelihood_df = attr(reml_loglik, "df"),
  reml_aic = AIC(model$lme),
  reml_bic = BIC(model$lme),
  overall_num_df = overall_test$numDF[1],
  overall_den_df = overall_test$denDF[1],
  overall_f = overall_test$`F-value`[1],
  overall_p = pf(
    overall_test$`F-value`[1],
    overall_test$numDF[1],
    overall_test$denDF[1],
    lower.tail = FALSE
  ),
  ar1_phi = unname(coef(model$lme$modelStruct$corStruct, unconstrained = FALSE)[1]),
  formula = paste(
    "butterfly_difference_cbrt ~ total_butterflies_t_lag +",
    "max_gust * temperature_avg * butterflies_direct_sun_t_lag"
  )
)
write_csv(fit_statistics, file.path(table_dir, "m16_fit_statistics.csv"))

# Conditional effect of a 1 m/s increase in wind
temperature_values <- c(10, 15, 20)
sun_values <- c(0, 7, 20)
fixed_beta <- fixef(model$lme)
fixed_vcov <- vcov(model$lme)
fixed_df <- min(lme_summary$tTable[, "DF"])

conditional_wind_effect <- function(temperature, direct_sun) {
  contrast <- setNames(rep(0, length(fixed_beta)), names(fixed_beta))
  contrast["Xmax_gust"] <- 1
  contrast["Xmax_gust:temperature_avg"] <- temperature
  contrast["Xmax_gust:butterflies_direct_sun_t_lag"] <- direct_sun
  contrast["Xmax_gust:temperature_avg:butterflies_direct_sun_t_lag"] <-
    temperature * direct_sun
  estimate <- sum(contrast * fixed_beta)
  standard_error <- sqrt(as.numeric(t(contrast) %*% fixed_vcov %*% contrast))
  t_value <- estimate / standard_error
  tibble(
    temperature_c = temperature,
    butterflies_in_direct_sun = direct_sun,
    wind_effect_per_1_ms = estimate,
    standard_error = standard_error,
    denominator_df = fixed_df,
    t_value = t_value,
    p_value = 2 * pt(abs(t_value), df = fixed_df, lower.tail = FALSE),
    conf_low = estimate + qt(0.025, df = fixed_df) * standard_error,
    conf_high = estimate + qt(0.975, df = fixed_df) * standard_error
  )
}

conditional_table <- bind_rows(lapply(temperature_values, function(temp) {
  bind_rows(lapply(sun_values, function(sun) conditional_wind_effect(temp, sun)))
}))
write_csv(
  conditional_table,
  file.path(table_dir, "m16_conditional_wind_effects.csv")
)

# Prediction data for manuscript-style figures
previous_bi_value <- median(data$total_butterflies_t_lag)
wind_max_plot <- unname(quantile(data$max_gust, 0.99))
wind_sequence <- seq(0, wind_max_plot, length.out = 160)

prediction_grid <- expand.grid(
  max_gust = wind_sequence,
  temperature_avg = temperature_values,
  butterflies_direct_sun_t_lag = sun_values,
  KEEP.OUT.ATTRS = FALSE
) %>%
  mutate(total_butterflies_t_lag = previous_bi_value)

prediction <- predict(model$gam, newdata = prediction_grid, se.fit = TRUE)
prediction_grid <- prediction_grid %>%
  mutate(
    fit = as.numeric(prediction$fit),
    standard_error = as.numeric(prediction$se.fit),
    conf_low = fit - 1.96 * standard_error,
    conf_high = fit + 1.96 * standard_error,
    temperature_label = factor(
      temperature_avg,
      levels = temperature_values,
      labels = c("10 °C", "15 °C", "20 °C")
    ),
    direct_sun_label = factor(
      butterflies_direct_sun_t_lag,
      levels = sun_values,
      labels = c("0", "7", "20")
    )
  )
write_csv(prediction_grid, file.path(table_dir, "m16_figure_predictions.csv"))

figure_theme <- theme_like_reference(12, 0.95) +
  theme(
    legend.position = "bottom",
    legend.title = element_text(size = reference_sizes(12, 0.95)$legend_title),
    strip.text = element_text(
      color = "black",
      size = reference_sizes(12, 0.95)$axis_text
    )
  )

sun_colors <- c("0" = "#4d4d4d", "7" = "#2b83ba", "20" = "#d7191c")

inside_polygon <- function(x, y, polygon_x, polygon_y) {
  inside <- rep(FALSE, length(x))
  previous <- length(polygon_x)
  for (current in seq_along(polygon_x)) {
    crosses <- ((polygon_y[current] > y) != (polygon_y[previous] > y)) &
      (x < (polygon_x[previous] - polygon_x[current]) *
        (y - polygon_y[current]) /
        (polygon_y[previous] - polygon_y[current]) + polygon_x[current])
    inside <- xor(inside, crosses)
    previous <- current
  }
  inside
}

inside_observed_hull <- function(x, y, observed_x, observed_y) {
  observed <- unique(data.frame(x = observed_x, y = observed_y))
  if (nrow(observed) < 3) return(rep(FALSE, length(x)))
  hull_rows <- chull(observed$x, observed$y)
  inside_polygon(
    x,
    y,
    observed$x[hull_rows],
    observed$y[hull_rows]
  )
}

prediction_plot <- ggplot(
  prediction_grid,
  aes(x = max_gust, y = fit, color = direct_sun_label, fill = direct_sun_label)
) +
  geom_ribbon(
    aes(ymin = conf_low, ymax = conf_high),
    alpha = 0.10,
    linewidth = 0,
    color = NA
  ) +
  geom_line(linewidth = 1.0) +
  geom_hline(yintercept = 0, color = "gray55", linewidth = 0.5) +
  facet_wrap(~temperature_label, nrow = 1) +
  scale_color_manual(values = sun_colors, name = "Butterflies visible in direct sun") +
  scale_fill_manual(values = sun_colors, name = "Butterflies visible in direct sun") +
  scale_x_continuous(expand = expansion(mult = c(0, 0.02))) +
  labs(
    x = "Maximum wind gust (m/s)",
    y = expression(paste("Predicted cube-root ", Delta, "BI"))
  ) +
  figure_theme

ggsave(
  file.path(candidate_figure_dir, "a_global_range_lines.png"),
  prediction_plot,
  width = 12,
  height = 5.8,
  dpi = 300,
  bg = "white"
)

# Candidate B. Familiar line plot, but each line is limited to the central 90
# percent of gusts among the 50 observations nearest to that temperature and
# direct-sun combination.
prediction_grid$supported <- FALSE
prediction_grid$supported_90 <- FALSE
temperature_scale <- sd(data$temperature_avg)
direct_sun_scale <- IQR(
  data$butterflies_direct_sun_t_lag[data$butterflies_direct_sun_t_lag > 0]
)
line_support_rows <- list()
for (temperature_value in temperature_values) {
  for (direct_sun_value in sun_values) {
    condition_distance <- sqrt(
      ((data$temperature_avg - temperature_value) / temperature_scale)^2 +
      ((data$butterflies_direct_sun_t_lag - direct_sun_value) /
        direct_sun_scale)^2
    )
    nearby_rows <- order(condition_distance)[seq_len(50)]
    supported_wind <- quantile(
      data$max_gust[nearby_rows],
      c(0.05, 0.95),
      names = FALSE
    )
    supported_wind_95 <- quantile(
      data$max_gust[nearby_rows],
      c(0.025, 0.975),
      names = FALSE
    )
    grid_rows <- prediction_grid$temperature_avg == temperature_value &
      prediction_grid$butterflies_direct_sun_t_lag == direct_sun_value
    prediction_grid$supported_90[grid_rows] <-
      prediction_grid$max_gust[grid_rows] >= supported_wind[1] &
      prediction_grid$max_gust[grid_rows] <= supported_wind[2]
    prediction_grid$supported[grid_rows] <-
      prediction_grid$max_gust[grid_rows] >= min(data$max_gust[nearby_rows]) &
      prediction_grid$max_gust[grid_rows] <= max(data$max_gust[nearby_rows])
    line_support_rows[[length(line_support_rows) + 1]] <- tibble(
      temperature_c = temperature_value,
      butterflies_in_direct_sun = direct_sun_value,
      nearby_observations = length(nearby_rows),
      wind_minimum = min(data$max_gust[nearby_rows]),
      wind_lower_95 = supported_wind_95[1],
      wind_lower = supported_wind[1],
      wind_upper = supported_wind[2],
      wind_upper_95 = supported_wind_95[2],
      wind_maximum = max(data$max_gust[nearby_rows])
    )
  }
}
line_support_table <- bind_rows(line_support_rows)

supported_prediction_grid <- prediction_grid %>%
  mutate(
    fit_supported = if_else(supported, fit, NA_real_),
    conf_low_supported = if_else(supported, conf_low, NA_real_),
    conf_high_supported = if_else(supported, conf_high, NA_real_),
    fit_supported_90 = if_else(supported_90, fit, NA_real_),
    conf_low_supported_90 = if_else(supported_90, conf_low, NA_real_),
    conf_high_supported_90 = if_else(supported_90, conf_high, NA_real_),
    fit_supported_raw = fit_supported^3,
    conf_low_supported_raw = conf_low_supported^3,
    conf_high_supported_raw = conf_high_supported^3
  )

supported_line_plot <- ggplot(
  supported_prediction_grid,
  aes(
    x = max_gust,
    y = fit_supported,
    color = direct_sun_label,
    fill = direct_sun_label,
    group = direct_sun_label
  )
) +
  geom_ribbon(
    aes(ymin = conf_low_supported, ymax = conf_high_supported),
    alpha = 0.10,
    linewidth = 0,
    color = NA,
    na.rm = TRUE
  ) +
  geom_line(linewidth = 1.0, na.rm = TRUE) +
  geom_hline(yintercept = 0, color = "gray55", linewidth = 0.5) +
  facet_wrap(~temperature_label, nrow = 1) +
  scale_color_manual(values = sun_colors, name = "Butterflies visible in direct sun") +
  scale_fill_manual(values = sun_colors, name = "Butterflies visible in direct sun") +
  scale_x_continuous(expand = expansion(mult = c(0, 0.02))) +
  labs(
    x = "Maximum wind gust (m/s)",
    y = "Modeled 30-minute BI change\n(cube-root scale)"
  ) +
  figure_theme

ggsave(
  file.path(figure_dir, "m16_predicted_response.png"),
  supported_line_plot,
  width = 12,
  height = 5.8,
  dpi = 600,
  bg = "white"
)

supported_90_line_plot <- ggplot(
  supported_prediction_grid,
  aes(
    x = max_gust,
    y = fit_supported_90,
    color = direct_sun_label,
    fill = direct_sun_label,
    group = direct_sun_label
  )
) +
  geom_ribbon(
    aes(ymin = conf_low_supported_90, ymax = conf_high_supported_90),
    alpha = 0.10,
    linewidth = 0,
    color = NA,
    na.rm = TRUE
  ) +
  geom_line(linewidth = 1.0, na.rm = TRUE) +
  geom_hline(yintercept = 0, color = "gray55", linewidth = 0.5) +
  facet_wrap(~temperature_label, nrow = 1) +
  scale_color_manual(values = sun_colors, name = "Butterflies visible in direct sun") +
  scale_fill_manual(values = sun_colors, name = "Butterflies visible in direct sun") +
  scale_x_continuous(expand = expansion(mult = c(0, 0.02))) +
  labs(
    x = "Maximum wind gust (m/s)",
    y = "Modeled 30-minute BI change\n(cube-root scale)"
  ) +
  figure_theme

ggsave(
  file.path(candidate_figure_dir, "b_supported_range_lines.png"),
  supported_90_line_plot,
  width = 12,
  height = 5.8,
  dpi = 300,
  bg = "white"
)

# Candidate E. Same representative conditions as candidate B, but each line
# spans the full minimum-to-maximum gust range among all 50 nearby observations.
all_local_prediction_grid <- expand.grid(
  max_gust = seq(min(data$max_gust), max(data$max_gust), length.out = 240),
  temperature_avg = temperature_values,
  butterflies_direct_sun_t_lag = sun_values,
  KEEP.OUT.ATTRS = FALSE
) %>%
  mutate(total_butterflies_t_lag = previous_bi_value)

all_local_prediction <- predict(
  model$gam,
  newdata = all_local_prediction_grid,
  se.fit = TRUE
)
all_local_prediction_grid <- all_local_prediction_grid %>%
  mutate(
    fit = as.numeric(all_local_prediction$fit),
    standard_error = as.numeric(all_local_prediction$se.fit),
    conf_low = fit - 1.96 * standard_error,
    conf_high = fit + 1.96 * standard_error,
    temperature_label = factor(
      temperature_avg,
      levels = temperature_values,
      labels = c("10 °C", "15 °C", "20 °C")
    ),
    direct_sun_label = factor(
      butterflies_direct_sun_t_lag,
      levels = sun_values,
      labels = c("0", "7", "20")
    )
  ) %>%
  left_join(
    line_support_table,
    by = c(
      "temperature_avg" = "temperature_c",
      "butterflies_direct_sun_t_lag" = "butterflies_in_direct_sun"
    )
  ) %>%
  mutate(
    supported_all = max_gust >= wind_minimum & max_gust <= wind_maximum,
    supported_95 = max_gust >= wind_lower_95 & max_gust <= wind_upper_95,
    fit_supported_all = if_else(supported_all, fit, NA_real_),
    conf_low_supported_all = if_else(supported_all, conf_low, NA_real_),
    conf_high_supported_all = if_else(supported_all, conf_high, NA_real_),
    fit_supported_95 = if_else(supported_95, fit, NA_real_),
    conf_low_supported_95 = if_else(supported_95, conf_low, NA_real_),
    conf_high_supported_95 = if_else(supported_95, conf_high, NA_real_)
  )

all_local_line_plot <- ggplot(
  all_local_prediction_grid,
  aes(
    x = max_gust,
    y = fit_supported_all,
    color = direct_sun_label,
    fill = direct_sun_label,
    group = direct_sun_label
  )
) +
  geom_ribbon(
    aes(ymin = conf_low_supported_all, ymax = conf_high_supported_all),
    alpha = 0.10,
    linewidth = 0,
    color = NA,
    na.rm = TRUE
  ) +
  geom_line(linewidth = 1.0, na.rm = TRUE) +
  geom_hline(yintercept = 0, color = "gray55", linewidth = 0.5) +
  facet_wrap(~temperature_label, nrow = 1) +
  scale_color_manual(values = sun_colors, name = "Butterflies visible in direct sun") +
  scale_fill_manual(values = sun_colors, name = "Butterflies visible in direct sun") +
  scale_x_continuous(
    breaks = seq(0, 12, by = 4),
    expand = expansion(mult = c(0, 0.02))
  ) +
  labs(
    x = "Maximum wind gust (m/s)",
    y = "Modeled 30-minute BI change\n(cube-root scale)"
  ) +
  figure_theme

ggsave(
  file.path(candidate_figure_dir, "e_all_local_range_lines.png"),
  all_local_line_plot,
  width = 12,
  height = 5.8,
  dpi = 300,
  bg = "white"
)

# Candidate F. Same design using the central 95 percent of gust values among
# the 50 nearby observations for each displayed condition.
supported_95_line_plot <- ggplot(
  all_local_prediction_grid,
  aes(
    x = max_gust,
    y = fit_supported_95,
    color = direct_sun_label,
    fill = direct_sun_label,
    group = direct_sun_label
  )
) +
  geom_ribbon(
    aes(ymin = conf_low_supported_95, ymax = conf_high_supported_95),
    alpha = 0.10,
    linewidth = 0,
    color = NA,
    na.rm = TRUE
  ) +
  geom_line(linewidth = 1.0, na.rm = TRUE) +
  geom_hline(yintercept = 0, color = "gray55", linewidth = 0.5) +
  facet_wrap(~temperature_label, nrow = 1) +
  scale_color_manual(values = sun_colors, name = "Butterflies visible in direct sun") +
  scale_fill_manual(values = sun_colors, name = "Butterflies visible in direct sun") +
  scale_x_continuous(
    breaks = seq(0, 12, by = 4),
    expand = expansion(mult = c(0, 0.02))
  ) +
  labs(
    x = "Maximum wind gust (m/s)",
    y = "Modeled 30-minute BI change\n(cube-root scale)"
  ) +
  figure_theme

ggsave(
  file.path(candidate_figure_dir, "f_95_percent_local_range_lines.png"),
  supported_95_line_plot,
  width = 12,
  height = 5.8,
  dpi = 300,
  bg = "white"
)

# Candidate G. Add the nonzero 25th percentile while retaining the median and
# 75th percentile. Lines span their full local range subject to the shared
# overall 99th-percentile gust cap used in the manuscript figure.
four_sun_values <- c(0, 3, 7, 20)
four_sun_prediction_grid <- expand.grid(
  max_gust = wind_sequence,
  temperature_avg = temperature_values,
  butterflies_direct_sun_t_lag = four_sun_values,
  KEEP.OUT.ATTRS = FALSE
) %>%
  mutate(total_butterflies_t_lag = previous_bi_value)

four_sun_prediction <- predict(
  model$gam,
  newdata = four_sun_prediction_grid,
  se.fit = TRUE
)
four_sun_prediction_grid <- four_sun_prediction_grid %>%
  mutate(
    fit = as.numeric(four_sun_prediction$fit),
    standard_error = as.numeric(four_sun_prediction$se.fit),
    conf_low = fit - 1.96 * standard_error,
    conf_high = fit + 1.96 * standard_error,
    supported = FALSE,
    temperature_label = factor(
      temperature_avg,
      levels = temperature_values,
      labels = c("10 °C", "15 °C", "20 °C")
    ),
    direct_sun_label = factor(
      butterflies_direct_sun_t_lag,
      levels = four_sun_values,
      labels = c("0", "3", "7", "20")
    )
  )

for (temperature_value in temperature_values) {
  for (direct_sun_value in four_sun_values) {
    condition_distance <- sqrt(
      ((data$temperature_avg - temperature_value) / temperature_scale)^2 +
      ((data$butterflies_direct_sun_t_lag - direct_sun_value) /
        direct_sun_scale)^2
    )
    nearby_rows <- order(condition_distance)[seq_len(50)]
    grid_rows <- four_sun_prediction_grid$temperature_avg == temperature_value &
      four_sun_prediction_grid$butterflies_direct_sun_t_lag == direct_sun_value
    four_sun_prediction_grid$supported[grid_rows] <-
      four_sun_prediction_grid$max_gust[grid_rows] >=
        min(data$max_gust[nearby_rows]) &
      four_sun_prediction_grid$max_gust[grid_rows] <=
        max(data$max_gust[nearby_rows])
  }
}

four_sun_prediction_grid <- four_sun_prediction_grid %>%
  mutate(
    fit_supported = if_else(supported, fit, NA_real_),
    conf_low_supported = if_else(supported, conf_low, NA_real_),
    conf_high_supported = if_else(supported, conf_high, NA_real_)
  )

four_sun_colors <- c(
  "0" = "#4d4d4d",
  "3" = "#009E73",
  "7" = "#0072B2",
  "20" = "#D55E00"
)
four_sun_line_plot <- ggplot(
  four_sun_prediction_grid,
  aes(
    x = max_gust,
    y = fit_supported,
    color = direct_sun_label,
    fill = direct_sun_label,
    group = direct_sun_label
  )
) +
  geom_ribbon(
    aes(ymin = conf_low_supported, ymax = conf_high_supported),
    alpha = 0.07,
    linewidth = 0,
    color = NA,
    na.rm = TRUE
  ) +
  geom_line(linewidth = 1.0, na.rm = TRUE) +
  geom_hline(yintercept = 0, color = "gray55", linewidth = 0.5) +
  facet_wrap(~temperature_label, nrow = 1) +
  scale_color_manual(values = four_sun_colors, name = "Butterflies visible in direct sun") +
  scale_fill_manual(values = four_sun_colors, name = "Butterflies visible in direct sun") +
  scale_x_continuous(expand = expansion(mult = c(0, 0.02))) +
  labs(
    x = "Maximum wind gust (m/s)",
    y = "Modeled 30-minute BI change\n(cube-root scale)"
  ) +
  figure_theme

ggsave(
  file.path(candidate_figure_dir, "g_four_direct_sun_levels.png"),
  four_sun_line_plot,
  width = 12,
  height = 5.8,
  dpi = 300,
  bg = "white"
)

# Candidate C. Three temperature slices through the fitted response surface.
# Gray regions lack nearby observations in wind and direct-sun space within
# 1.5 degrees C of the displayed temperature.
surface_sun_max <- unname(quantile(
  data$butterflies_direct_sun_t_lag[data$butterflies_direct_sun_t_lag > 0],
  0.95
))
surface_grid <- expand.grid(
  max_gust = seq(0, wind_max_plot, length.out = 120),
  temperature_avg = temperature_values,
  butterflies_direct_sun_t_lag = seq(0, surface_sun_max, length.out = 120),
  KEEP.OUT.ATTRS = FALSE
) %>%
  mutate(total_butterflies_t_lag = previous_bi_value)

surface_prediction <- predict(model$gam, newdata = surface_grid, se.fit = TRUE)
surface_grid <- surface_grid %>%
  mutate(
    fit = as.numeric(surface_prediction$fit),
    supported = FALSE,
    temperature_label = factor(
      temperature_avg,
      levels = temperature_values,
      labels = c("10 °C", "15 °C", "20 °C")
    )
  )
for (temperature_value in temperature_values) {
  grid_rows <- surface_grid$temperature_avg == temperature_value
  nearby_data <- data %>%
    filter(abs(temperature_avg - temperature_value) <= 1.5)
  surface_grid$supported[grid_rows] <- inside_observed_hull(
    surface_grid$max_gust[grid_rows],
    surface_grid$butterflies_direct_sun_t_lag[grid_rows],
    nearby_data$max_gust,
    nearby_data$butterflies_direct_sun_t_lag
  )
}
surface_grid <- surface_grid %>%
  mutate(fit_supported = if_else(supported, fit, NA_real_))

surface_points <- bind_rows(lapply(temperature_values, function(temperature_value) {
  data %>%
    filter(
      abs(temperature_avg - temperature_value) <= 1.5,
      max_gust <= wind_max_plot,
      butterflies_direct_sun_t_lag <= surface_sun_max
    ) %>%
    mutate(
      temperature_label = factor(
        temperature_value,
        levels = temperature_values,
        labels = c("10 °C", "15 °C", "20 °C")
      )
    )
}))

surface_limit <- max(abs(surface_grid$fit_supported), na.rm = TRUE)
response_surface_plot <- ggplot(
  surface_grid,
  aes(x = max_gust, y = butterflies_direct_sun_t_lag)
) +
  geom_raster(aes(fill = fit_supported)) +
  geom_point(
    data = surface_points,
    aes(x = max_gust, y = butterflies_direct_sun_t_lag),
    inherit.aes = FALSE,
    shape = 21,
    fill = "white",
    color = "gray25",
    alpha = 0.28,
    size = 0.8,
    stroke = 0.2
  ) +
  facet_wrap(~temperature_label, nrow = 1) +
  scale_fill_gradient2(
    low = "#2b83ba",
    mid = "white",
    high = "#d7191c",
    midpoint = 0,
    limits = c(-surface_limit, surface_limit),
    na.value = "gray88",
    name = expression(paste("Predicted cube-root ", Delta, "BI"))
  ) +
  labs(
    x = "Maximum wind gust (m/s)",
    y = "Butterflies visible in direct sun"
  ) +
  figure_theme +
  theme(legend.position = "right")

ggsave(
  file.path(candidate_figure_dir, "c_supported_response_surfaces.png"),
  response_surface_plot,
  width = 12,
  height = 5.8,
  dpi = 300,
  bg = "white"
)

# Conditional wind-effect figure with simultaneous conditions shown separately
slope_sun_sequence <- seq(
  0,
  unname(quantile(
    data$butterflies_direct_sun_t_lag[data$butterflies_direct_sun_t_lag > 0],
    0.95
  )),
  length.out = 180
)
slope_grid <- bind_rows(lapply(temperature_values, function(temp) {
  bind_rows(lapply(slope_sun_sequence, function(sun) {
    conditional_wind_effect(temp, sun)
  }))
})) %>%
  mutate(
    temperature_label = factor(
      temperature_c,
      levels = temperature_values,
      labels = c("10 °C", "15 °C", "20 °C")
    )
  )
write_csv(slope_grid, file.path(table_dir, "m16_conditional_wind_effect_curve.csv"))

slope_plot <- ggplot(
  slope_grid,
  aes(x = butterflies_in_direct_sun, y = wind_effect_per_1_ms)
) +
  geom_ribbon(
    aes(ymin = conf_low, ymax = conf_high),
    fill = "#9ecae1",
    alpha = 0.35
  ) +
  geom_line(color = "#2b83ba", linewidth = 1.1) +
  geom_hline(yintercept = 0, color = "gray45", linewidth = 0.6) +
  facet_wrap(~temperature_label, nrow = 1) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.02))) +
  labs(
    x = "Butterflies visible in direct sun",
    y = "Wind effect per 1 m/s"
  ) +
  figure_theme +
  theme(legend.position = "none")

ggsave(
  file.path(figure_dir, "m16_conditional_wind_effect.png"),
  slope_plot,
  width = 12,
  height = 5.8,
  dpi = 600,
  bg = "white"
)

# Candidate D. Conditional wind slope across temperature and the direct-sun
# measure. This removes arbitrary slices and displays the three-way interaction
# directly. Gray regions lack nearby observed temperature and sun combinations.
slope_surface_grid <- expand.grid(
  temperature_c = seq(
    unname(quantile(data$temperature_avg, 0.01)),
    unname(quantile(data$temperature_avg, 0.99)),
    length.out = 180
  ),
  butterflies_in_direct_sun = seq(0, surface_sun_max, length.out = 180),
  KEEP.OUT.ATTRS = FALSE
)

contrast_matrix <- matrix(
  0,
  nrow = nrow(slope_surface_grid),
  ncol = length(fixed_beta),
  dimnames = list(NULL, names(fixed_beta))
)
contrast_matrix[, "Xmax_gust"] <- 1
contrast_matrix[, "Xmax_gust:temperature_avg"] <-
  slope_surface_grid$temperature_c
contrast_matrix[, "Xmax_gust:butterflies_direct_sun_t_lag"] <-
  slope_surface_grid$butterflies_in_direct_sun
contrast_matrix[, "Xmax_gust:temperature_avg:butterflies_direct_sun_t_lag"] <-
  slope_surface_grid$temperature_c *
  slope_surface_grid$butterflies_in_direct_sun

slope_surface_grid$estimate <- as.numeric(contrast_matrix %*% fixed_beta)
slope_surface_grid$standard_error <- sqrt(rowSums(
  (contrast_matrix %*% fixed_vcov) * contrast_matrix
))
slope_surface_grid$conf_low <- slope_surface_grid$estimate +
  qt(0.025, df = fixed_df) * slope_surface_grid$standard_error
slope_surface_grid$conf_high <- slope_surface_grid$estimate +
  qt(0.975, df = fixed_df) * slope_surface_grid$standard_error
slope_surface_grid$supported <- inside_observed_hull(
  slope_surface_grid$temperature_c,
  slope_surface_grid$butterflies_in_direct_sun,
  data$temperature_avg,
  data$butterflies_direct_sun_t_lag
)
slope_surface_grid$estimate_supported <- if_else(
  slope_surface_grid$supported,
  slope_surface_grid$estimate,
  NA_real_
)

slope_surface_points <- data %>%
  filter(
    butterflies_direct_sun_t_lag <= surface_sun_max,
    temperature_avg >= min(slope_surface_grid$temperature_c),
    temperature_avg <= max(slope_surface_grid$temperature_c)
  )

slope_limit <- max(abs(slope_surface_grid$estimate_supported), na.rm = TRUE)
conditional_surface_plot <- ggplot(
  slope_surface_grid,
  aes(x = temperature_c, y = butterflies_in_direct_sun)
) +
  geom_raster(aes(fill = estimate_supported)) +
  geom_contour(
    aes(z = estimate),
    breaks = 0,
    color = "gray20",
    linewidth = 0.7
  ) +
  geom_point(
    data = slope_surface_points,
    aes(x = temperature_avg, y = butterflies_direct_sun_t_lag),
    inherit.aes = FALSE,
    shape = 21,
    fill = "white",
    color = "gray25",
    alpha = 0.20,
    size = 0.8,
    stroke = 0.2
  ) +
  scale_fill_gradient2(
    low = "#2b83ba",
    mid = "white",
    high = "#d7191c",
    midpoint = 0,
    limits = c(-slope_limit, slope_limit),
    na.value = "gray88",
    name = "Wind slope per 1 m/s"
  ) +
  labs(
    x = "Approximate local temperature (°C)",
    y = "Butterflies visible in direct sun"
  ) +
  theme_like_reference(7, 0.95) +
  guides(fill = guide_colorbar(title.position = "top")) +
  theme(
    legend.position = "bottom",
    legend.title = element_text(size = reference_figure_style$legend_title),
    plot.margin = margin(8, 12, 8, 12)
  )

ggsave(
  file.path(candidate_figure_dir, "d_conditional_wind_effect_surface.png"),
  conditional_surface_plot,
  width = 8.5,
  height = 6.5,
  dpi = 300,
  bg = "white"
)

write_csv(
  supported_prediction_grid,
  file.path(table_dir, "m16_supported_line_predictions.csv")
)
write_csv(
  line_support_table,
  file.path(table_dir, "m16_supported_line_ranges.csv")
)
write_csv(
  all_local_prediction_grid,
  file.path(table_dir, "m16_all_local_line_predictions.csv")
)
write_csv(
  four_sun_prediction_grid,
  file.path(table_dir, "m16_four_sun_level_predictions.csv")
)
write_csv(
  surface_grid,
  file.path(table_dir, "m16_supported_response_surface.csv")
)
write_csv(
  slope_surface_grid,
  file.path(table_dir, "m16_conditional_wind_effect_surface.csv")
)

# Model diagnostics
residual_data <- tibble(
  fitted = fitted(model$lme),
  residual = residuals(model$lme, type = "normalized")
)
diagnostic_theme <- theme_like_reference(9, 0.80)
diagnostic_plot <- wrap_plots(
  ggplot(residual_data, aes(sample = residual)) +
    stat_qq(alpha = 0.25, size = 0.8, color = "#4d4d4d") +
    stat_qq_line(color = "#2c7fb8", linewidth = 0.8) +
    labs(x = "Theoretical quantiles", y = "Sample quantiles") +
    diagnostic_theme,
  ggplot(residual_data, aes(fitted, residual)) +
    geom_point(alpha = 0.25, size = 0.8, color = "#4d4d4d") +
    geom_smooth(
      se = FALSE,
      color = "#2c7fb8",
      linewidth = 0.8,
      method = "loess",
      span = 0.8
    ) +
    geom_hline(yintercept = 0, color = "gray65") +
    labs(x = "Fitted values", y = "Standardized residuals") +
    diagnostic_theme,
  nrow = 1
)
ggsave(
  file.path(figure_dir, "m16_diagnostics.png"),
  diagnostic_plot,
  width = 9,
  height = 5,
  dpi = 600,
  bg = "white"
)

acf_cex <- acf_cex_like_reference(7, 0.70)
png(
  file.path(figure_dir, "m16_residual_acf.png"),
  width = 7,
  height = 5,
  units = "in",
  res = 600
)
par(
  cex.lab = acf_cex$lab,
  cex.axis = acf_cex$axis,
  cex.main = acf_cex$lab,
  mar = c(5, 5, 2, 2)
)
acf(
  residual_data$residual,
  main = "",
  xlab = "Lag",
  ylab = "Autocorrelation"
)
dev.off()

png(
  file.path(figure_dir, "m16_residual_pacf.png"),
  width = 7,
  height = 5,
  units = "in",
  res = 600
)
par(
  cex.lab = acf_cex$lab,
  cex.axis = acf_cex$axis,
  cex.main = acf_cex$lab,
  mar = c(5, 5, 2, 2)
)
pacf(
  residual_data$residual,
  main = "",
  xlab = "Lag",
  ylab = "Partial autocorrelation"
)
dev.off()

diagnostic_statistics <- tibble(
  residual_mean = mean(residual_data$residual),
  residual_standard_deviation = sd(residual_data$residual),
  normalized_residual_acf_lag_1 = as.numeric(
    acf(residual_data$residual, plot = FALSE)$acf[2]
  ),
  normalized_residual_pacf_lag_1 = as.numeric(
    pacf(residual_data$residual, plot = FALSE)$acf[1]
  )
)
write_csv(
  diagnostic_statistics,
  file.path(table_dir, "m16_diagnostic_statistics.csv")
)

# Full text outputs and figure notes
full_summary <- capture.output({
  cat("M16 formula\n")
  print(model_formula)
  cat("\nREML GAM summary\n")
  print(gam_summary)
  cat("\nREML mixed-model summary\n")
  print(lme_summary)
  cat("\nFixed-effect 95 percent confidence intervals\n")
  print(intervals(model$lme, which = "fixed")$fixed)
  cat("\nVariance components\n")
  print(VarCorr(model$lme))
  cat("\nAR1 coefficient\n")
  print(coef(model$lme$modelStruct$corStruct, unconstrained = FALSE))
  cat("\nML model-comparison statistics\n")
  print(m16_audit)
})
writeLines(
  trimws(full_summary, which = "right"),
  file.path(text_dir, "m16_full_summary.txt")
)

figure_notes <- c(
  "M16 figure conditions",
  "",
  paste("Previous BI is held at the sample median of", previous_bi_value, "butterflies."),
  paste(
    "Temperature values represent a cool observed condition, a representative",
    "value within the historical flight-threshold range, and a warm observed condition:",
    paste(temperature_values, collapse = ", "), "degrees C."
  ),
  paste(
    "Direct-sun values represent no visible butterflies in direct sun and the",
    "median and 75th percentile among nonzero direct-sun observations:",
    paste(sun_values, collapse = ", "), "butterflies."
  ),
  paste(
    "The wind range ends at the 99th percentile of the observed maximum gust",
    paste0("distribution, ", round(wind_max_plot, 2), " m/s.")
  ),
  paste(
    "The manuscript figure shows fitted values on the signed cube-root response scale.",
    "Values above zero indicate increases in BI and values below zero indicate decreases."
  ),
  paste(
    "Each manuscript line spans the full local gust range among the 50 nearest",
    "observations, subject to the shared overall 99th-percentile cap."
  ),
  "All observations, including those above the plotting cap, were retained in model fitting.",
  "Predictions exclude random effects. Confidence bands are pointwise 95 percent fixed-effect intervals.",
  paste(
    "Candidate B limits each line to the central 90 percent of gusts among",
    "the 50 observations nearest to its temperature and direct-sun combination."
  ),
  paste(
    "Candidate E spans the full minimum-to-maximum gust range among all",
    "50 nearby observations for each temperature and direct-sun combination."
  ),
  paste(
    "Candidate F spans the central 95 percent of gust values among the",
    "50 nearby observations for each temperature and direct-sun combination."
  ),
  paste(
    "Candidate G adds the nonzero 25th percentile, using direct-sun values",
    "of 0, 3, 7, and 20 butterflies with the manuscript range rules."
  ),
  paste(
    "Candidate C masks predictions outside the convex hull of wind and",
    "direct-sun observations within 1.5 degrees C of each displayed temperature."
  ),
  paste(
    "Candidate D masks conditional wind slopes outside the convex hull of",
    "observed temperature and direct-sun combinations."
  ),
  "Raw main-effect coefficients are conditional on zero values of interacting predictors.",
  "Temperature zero is outside the observed range, so the interaction figures should guide interpretation."
)
writeLines(figure_notes, file.path(text_dir, "m16_figure_notes.txt"))

writeLines(
  trimws(capture.output(sessionInfo()), which = "right"),
  file.path(text_dir, "session_info.txt")
)

message("Wrote complete M16 outputs to ", out_dir)
