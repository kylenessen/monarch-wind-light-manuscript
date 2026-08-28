#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(here)
  library(mgcv)
  library(nlme)
  library(purrr)
  library(readr)
  library(tibble)
})

input_dir <- here("analysis", "outputs", "bi_category_sensitivity", "data")
output_dir <- here("analysis", "outputs", "bi_category_sensitivity")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

mapping_names <- c(
  "lower_bound", "geometric_midpoint", "arithmetic_midpoint", "upper_bound"
)

fit_gamm <- function(formula, data, random, correlation, method) {
  warnings <- character()
  fit <- withCallingHandlers(
    gamm(
      formula,
      data = data,
      random = random,
      correlation = correlation,
      method = method
    ),
    warning = function(w) {
      warnings <<- c(warnings, conditionMessage(w))
      invokeRestart("muffleWarning")
    }
  )
  list(fit = fit, warnings = paste(unique(warnings), collapse = " | "))
}

aicc <- function(fit, n) {
  likelihood <- logLik(fit$lme)
  k <- attr(likelihood, "df")
  AIC(fit$lme) + 2 * k * (k + 1) / (n - k - 1)
}

conditional_wind_effect <- function(fit, temperature, direct_sun) {
  beta <- fixef(fit$lme)
  covariance <- vcov(fit$lme)
  contrast <- setNames(rep(0, length(beta)), names(beta))
  contrast["Xmax_gust"] <- 1
  contrast["Xmax_gust:temperature_avg"] <- temperature
  contrast["Xmax_gust:butterflies_direct_sun_t_lag"] <- direct_sun
  contrast["Xmax_gust:temperature_avg:butterflies_direct_sun_t_lag"] <-
    temperature * direct_sun
  estimate <- sum(contrast * beta)
  standard_error <- sqrt(as.numeric(t(contrast) %*% covariance %*% contrast))
  denominator_df <- min(summary(fit$lme)$tTable[, "DF"])
  t_value <- estimate / standard_error
  tibble(
    temperature_c = temperature,
    direct_sun_bi = direct_sun,
    estimate = estimate,
    standard_error = standard_error,
    p_value = 2 * pt(abs(t_value), df = denominator_df, lower.tail = FALSE)
  )
}

analyze_30_minute <- function(mapping) {
  data <- read_csv(
    file.path(input_dir, paste0("30_minute_", mapping, ".csv")),
    show_col_types = FALSE
  ) %>%
    filter(complete.cases(
      butterfly_difference_cbrt, total_butterflies_t_lag,
      temperature_avg, max_gust, butterflies_direct_sun_t_lag,
      observation_order_within_day_t, deployment_day, deployment_id
    ))

  random <- list(deployment_id = ~1, deployment_day = ~1)
  correlation <- corAR1(
    form = ~ observation_order_within_day_t | deployment_day
  )
  formulas <- list(
    m15 = butterfly_difference_cbrt ~ total_butterflies_t_lag +
      max_gust * temperature_avg +
      max_gust * butterflies_direct_sun_t_lag +
      temperature_avg * butterflies_direct_sun_t_lag,
    m16 = butterfly_difference_cbrt ~ total_butterflies_t_lag +
      max_gust * temperature_avg * butterflies_direct_sun_t_lag,
    m40 = butterfly_difference_cbrt ~
      max_gust * temperature_avg * butterflies_direct_sun_t_lag
  )
  ml <- map(formulas, ~ fit_gamm(.x, data, random, correlation, "ML"))
  reml <- fit_gamm(formulas$m16, data, random, correlation, "REML")
  coefficients <- summary(reml$fit$lme)$tTable
  interaction_row <- coefficients[
    "Xmax_gust:temperature_avg:butterflies_direct_sun_t_lag",
  ]

  nonzero_sun <- data$butterflies_direct_sun_t_lag[
    data$butterflies_direct_sun_t_lag > 0
  ]
  sun_values <- c(
    0,
    unname(median(nonzero_sun)),
    unname(quantile(nonzero_sun, 0.75))
  )
  conditional <- map_dfr(c(10, 15, 20), function(temperature) {
    map_dfr(sun_values, function(direct_sun) {
      conditional_wind_effect(reml$fit, temperature, direct_sun)
    })
  }) %>%
    mutate(mapping = mapping, .before = 1)

  summary_row <- tibble(
    mapping = mapping,
    n = nrow(data),
    nonzero_sun_median = sun_values[2],
    nonzero_sun_q75 = sun_values[3],
    m16_ml_aic = AIC(ml$m16$fit$lme),
    m15_minus_m16_aic = AIC(ml$m15$fit$lme) - AIC(ml$m16$fit$lme),
    m40_minus_m16_aic = AIC(ml$m40$fit$lme) - AIC(ml$m16$fit$lme),
    three_way_estimate = interaction_row["Value"],
    three_way_standard_error = interaction_row["Std.Error"],
    three_way_p_value = interaction_row["p-value"],
    adjusted_r_squared = summary(reml$fit$gam)$r.sq,
    ml_warning = ml$m16$warnings,
    reml_warning = reml$warnings
  )
  list(summary = summary_row, conditional = conditional)
}

analyze_next_day <- function(mapping) {
  data <- read_csv(
    file.path(input_dir, paste0("next_day_", mapping, ".csv")),
    show_col_types = FALSE
  ) %>%
    mutate(
      butterfly_diff_sqrt = sign(butterfly_diff) * sqrt(abs(butterfly_diff))
    ) %>%
    filter(metrics_complete >= 0.95) %>%
    arrange(deployment_id, observation_order_t) %>%
    filter(complete.cases(
      butterfly_diff_sqrt, max_butterflies_t_1, lag_duration_hours,
      wind_max_gust, sum_butterflies_direct_sun, deployment_id,
      observation_order_t
    ))

  random <- list(deployment_id = ~1)
  correlation <- corAR1(form = ~ observation_order_t | deployment_id)
  m2_formula <- butterfly_diff_sqrt ~
    max_butterflies_t_1 + lag_duration_hours
  m32_formula <- butterfly_diff_sqrt ~
    max_butterflies_t_1 + lag_duration_hours +
    ti(wind_max_gust, sum_butterflies_direct_sun)
  m2_ml <- fit_gamm(m2_formula, data, random, correlation, "ML")
  m32_ml <- fit_gamm(m32_formula, data, random, correlation, "ML")
  m32_reml <- fit_gamm(m32_formula, data, random, correlation, "REML")
  smooth_row <- summary(m32_reml$fit$gam)$s.table[
    "ti(wind_max_gust,sum_butterflies_direct_sun)",
  ]

  tibble(
    mapping = mapping,
    n = nrow(data),
    m32_ml_aicc = aicc(m32_ml$fit, nrow(data)),
    m2_minus_m32_aicc = aicc(m2_ml$fit, nrow(data)) -
      aicc(m32_ml$fit, nrow(data)),
    interaction_edf = smooth_row["edf"],
    interaction_f = smooth_row["F"],
    interaction_p_value = smooth_row["p-value"],
    adjusted_r_squared = summary(m32_reml$fit$gam)$r.sq,
    ml_warning = m32_ml$warnings,
    reml_warning = m32_reml$warnings
  )
}

analyze_observer_sensitivity <- function() {
  data <- read_csv(
    file.path(input_dir, "30_minute_lower_bound.csv"),
    show_col_types = FALSE
  ) %>%
    filter(complete.cases(
      butterfly_difference_cbrt, total_butterflies_t_lag,
      temperature_avg, max_gust, butterflies_direct_sun_t_lag,
      observation_order_within_day_t, deployment_day, deployment_id,
      Observer
    ))
  random <- list(deployment_id = ~1, deployment_day = ~1)
  correlation <- corAR1(
    form = ~ observation_order_within_day_t | deployment_day
  )
  baseline_formula <- butterfly_difference_cbrt ~
    total_butterflies_t_lag +
    max_gust * temperature_avg * butterflies_direct_sun_t_lag
  observer_formula <- butterfly_difference_cbrt ~
    Observer + total_butterflies_t_lag +
    max_gust * temperature_avg * butterflies_direct_sun_t_lag
  baseline <- fit_gamm(
    baseline_formula, data, random, correlation, "ML"
  )
  observer <- fit_gamm(
    observer_formula, data, random, correlation, "ML"
  )
  comparison <- anova(baseline$fit$lme, observer$fit$lme)
  coefficients <- summary(observer$fit$lme)$tTable
  interaction <- coefficients[
    "Xmax_gust:temperature_avg:butterflies_direct_sun_t_lag",
  ]
  tibble(
    baseline_aic = AIC(baseline$fit$lme),
    observer_fixed_aic = AIC(observer$fit$lme),
    observer_likelihood_ratio = comparison$L.Ratio[2],
    observer_likelihood_ratio_p_value = comparison$`p-value`[2],
    three_way_estimate = interaction["Value"],
    three_way_standard_error = interaction["Std.Error"],
    three_way_p_value = interaction["p-value"],
    baseline_warning = baseline$warnings,
    observer_warning = observer$warnings
  )
}

results_30 <- map(mapping_names, analyze_30_minute)
write_csv(
  map_dfr(results_30, "summary"),
  file.path(output_dir, "thirty_minute_sensitivity.csv")
)
write_csv(
  map_dfr(results_30, "conditional"),
  file.path(output_dir, "thirty_minute_conditional_effects.csv")
)
write_csv(
  map_dfr(mapping_names, analyze_next_day),
  file.path(output_dir, "next_day_sensitivity.csv")
)
write_csv(
  analyze_observer_sensitivity(),
  file.path(output_dir, "observer_fixed_effect_sensitivity.csv")
)
