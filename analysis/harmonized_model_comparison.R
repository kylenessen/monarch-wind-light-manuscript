#!/usr/bin/env Rscript

# Harmonized candidate-model comparison for the 30-minute and Next Day
# response windows. Environmental predictors retain their original definitions.

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(here)
  library(mgcv)
  library(nlme)
  library(purrr)
  library(readr)
  library(tibble)
})

source(here("analysis", "lib", "manuscript_figure_style.R"))

out_dir <- here("analysis", "outputs", "harmonized_model_comparison")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

fit_model_safe <- function(formula, data, random, correlation, method = "ML") {
  warnings <- character()
  tryCatch({
    model <- withCallingHandlers(
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
    list(model = model, error = "", warning = paste(unique(warnings), collapse = " | "))
  }, error = function(e) {
    list(model = NULL, error = conditionMessage(e), warning = paste(unique(warnings), collapse = " | "))
  })
}

add_spec <- function(specs, id, rhs, hypothesis, temperature_variant = "none",
                     legacy_model = "", mirror_of = "") {
  specs[[id]] <- list(
    id = id,
    rhs = rhs,
    hypothesis = hypothesis,
    temperature_variant = temperature_variant,
    legacy_model = legacy_model,
    mirror_of = mirror_of
  )
  specs
}

build_candidate_specs <- function(response, controls, wind, sun, temperatures, window) {
  specs <- list()
  join_terms <- function(...) paste(c(...), collapse = " + ")
  smooth <- function(x) paste0("s(", x, ", k = 5, bs = \"ts\")")
  tensor <- paste0("ti(", wind, ", ", sun, ")")

  specs <- add_spec(specs, "H00", controls, "Controls only")
  specs <- add_spec(specs, "H01", join_terms(controls, wind), "Wind")
  specs <- add_spec(specs, "H02", join_terms(controls, sun), "Sun-exposed BI")
  specs <- add_spec(specs, "H03", join_terms(controls, wind, sun), "Additive wind and sun-exposed BI")
  specs <- add_spec(
    specs, "H04", join_terms(controls, paste0(wind, " * ", sun)),
    "Linear wind by sun-exposed BI interaction"
  )
  specs <- add_spec(
    specs, "H05", join_terms(controls, tensor),
    "Centered tensor wind by sun-exposed BI interaction",
    legacy_model = if (window == "next_day") "M32" else "",
    mirror_of = if (window == "thirty_minute") "M32" else ""
  )
  specs <- add_spec(
    specs, "H06", join_terms(controls, smooth(wind), smooth(sun)),
    "Smooth additive wind and sun-exposed BI"
  )
  specs <- add_spec(
    specs, "H07", join_terms(controls, smooth(wind), smooth(sun), tensor),
    "Hierarchical tensor wind by sun-exposed BI interaction"
  )

  for (temperature_name in names(temperatures)) {
    temperature <- temperatures[[temperature_name]]
    prefix <- paste0(temperature_name, "_")
    legacy_three_way <- if (window == "thirty_minute") "M16" else ""
    mirror_three_way <- if (window == "next_day") "M16" else ""

    specs <- add_spec(
      specs, paste0(prefix, "T01"), join_terms(controls, temperature),
      "Temperature", temperature_name
    )
    specs <- add_spec(
      specs, paste0(prefix, "T02"), join_terms(controls, wind, temperature, sun),
      "Additive wind, temperature, and sun-exposed BI", temperature_name
    )
    specs <- add_spec(
      specs, paste0(prefix, "T03"),
      join_terms(controls, paste0(wind, " * ", temperature), sun),
      "Linear wind by temperature interaction", temperature_name
    )
    specs <- add_spec(
      specs, paste0(prefix, "T04"),
      join_terms(controls, paste0(wind, " * ", sun), temperature),
      "Linear wind by sun-exposed BI interaction with additive temperature",
      temperature_name
    )
    specs <- add_spec(
      specs, paste0(prefix, "T05"),
      join_terms(controls, paste0(temperature, " * ", sun), wind),
      "Linear temperature by sun-exposed BI interaction", temperature_name
    )
    specs <- add_spec(
      specs, paste0(prefix, "T06"),
      join_terms(
        controls,
        paste0(wind, " * ", temperature),
        paste0(wind, " * ", sun),
        paste0(temperature, " * ", sun)
      ),
      "All linear two-way interactions", temperature_name
    )
    specs <- add_spec(
      specs, paste0(prefix, "T07"),
      join_terms(controls, paste0(wind, " * ", temperature, " * ", sun)),
      "Linear wind by temperature by sun-exposed BI interaction",
      temperature_name, legacy_three_way, mirror_three_way
    )
    specs <- add_spec(
      specs, paste0(prefix, "T08"),
      join_terms(controls, smooth(wind), smooth(temperature), smooth(sun)),
      "Smooth additive wind, temperature, and sun-exposed BI", temperature_name
    )
    specs <- add_spec(
      specs, paste0(prefix, "T09"),
      join_terms(controls, smooth(wind), smooth(temperature), smooth(sun), tensor),
      "Hierarchical tensor wind by sun-exposed BI interaction with smooth temperature",
      temperature_name
    )
  }

  formulas <- vapply(specs, function(x) paste(response, "~", x$rhs), character(1))
  stopifnot(!anyDuplicated(formulas))
  specs
}

compare_candidates <- function(specs, response, data, random, correlation, window, framework) {
  rows <- map_dfr(specs, function(spec) {
    formula_string <- paste(response, "~", spec$rhs)
    fit <- fit_model_safe(as.formula(formula_string), data, random, correlation, method = "ML")
    has_convergence_warning <- grepl("convergence", fit$warning, ignore.case = TRUE)

    if (is.null(fit$model) || is.null(fit$model$lme) || has_convergence_warning) {
      return(tibble(
        window = window, framework = framework, candidate_id = spec$id,
        hypothesis = spec$hypothesis, temperature_variant = spec$temperature_variant,
        legacy_model = spec$legacy_model, mirror_of = spec$mirror_of,
        formula = formula_string,
        status = if (has_convergence_warning) "convergence_failure" else "failure",
        error = fit$error, warning = fit$warning, n = nrow(data), likelihood_method = "ML",
        AIC = NA_real_, BIC = NA_real_, logLik = NA_real_, df = NA_real_, AICc = NA_real_,
        delta_AICc = NA_real_, weight_AICc = NA_real_, rank_AICc = NA_integer_
      ))
    }

    log_likelihood <- logLik(fit$model$lme)
    df <- as.numeric(attr(log_likelihood, "df"))
    n <- as.integer(nobs(fit$model$lme))
    aic <- AIC(fit$model$lme)
    aicc <- if (n > df + 1) aic + (2 * df * (df + 1)) / (n - df - 1) else NA_real_

    tibble(
      window = window, framework = framework, candidate_id = spec$id,
      hypothesis = spec$hypothesis, temperature_variant = spec$temperature_variant,
      legacy_model = spec$legacy_model, mirror_of = spec$mirror_of,
      formula = formula_string, status = "success", error = "", warning = fit$warning,
      n = n, likelihood_method = "ML", AIC = aic, BIC = BIC(fit$model$lme),
      logLik = as.numeric(log_likelihood), df = df, AICc = aicc,
      delta_AICc = NA_real_, weight_AICc = NA_real_, rank_AICc = NA_integer_
    )
  })

  rankable <- rows$status == "success" & is.finite(rows$AICc)
  rows$delta_AICc[rankable] <- rows$AICc[rankable] - min(rows$AICc[rankable])
  rows$weight_AICc[rankable] <- exp(-0.5 * rows$delta_AICc[rankable]) /
    sum(exp(-0.5 * rows$delta_AICc[rankable]))
  ranked_indices <- which(rankable)[order(rows$AICc[rankable])]
  rows$rank_AICc[ranked_indices] <- seq_along(ranked_indices)
  rows
}

refit_selected <- function(comparison, data, random, correlation) {
  selected <- comparison %>%
    filter(status == "success", is.finite(AICc)) %>%
    arrange(AICc) %>%
    slice(1)
  fit <- fit_model_safe(as.formula(selected$formula), data, random, correlation, method = "REML")
  if (is.null(fit$model) || is.null(fit$model$lme) ||
      grepl("convergence", fit$warning, ignore.case = TRUE)) {
    stop("Selected REML refit failed for ", selected$window, " ", selected$framework)
  }

  model_summary <- summary(fit$model$gam)
  parametric <- as.data.frame(model_summary$p.table) %>%
    rownames_to_column("term") %>%
    as_tibble() %>%
    mutate(term_type = "parametric")
  smooth <- as.data.frame(model_summary$s.table) %>%
    rownames_to_column("term") %>%
    as_tibble() %>%
    mutate(term_type = "smooth")

  list(
    selected = selected,
    summary = bind_rows(parametric, smooth),
    model = fit$model,
    fit = tibble(
      window = selected$window,
      framework = selected$framework,
      candidate_id = selected$candidate_id,
      legacy_model = selected$legacy_model,
      formula = selected$formula,
      n = nrow(data),
      adjusted_r_squared = model_summary$r.sq,
      scale = model_summary$scale
    )
  )
}

thirty_minute_data <- read_csv(
  here("data", "analysis_inputs", "analysis_30_minute.csv"), show_col_types = FALSE
) %>%
  filter(
    !is.na(delta_bi_signed_cuberoot), !is.na(previous_bi),
    !is.na(maximum_wind_gust_m_s), !is.na(mean_temperature_c), !is.na(previous_sun_exposed_bi),
    !is.na(minutes_since_first_daily_observation), !is.na(observation_order),
    !is.na(deployment_day_id), !is.na(deployment_id)
  )

next_day_data <- read_csv(
  here("data", "analysis_inputs", "analysis_next_day.csv"), show_col_types = FALSE
) %>%
  mutate(
    delta_bi_signed_square_root = sign(delta_bi) * sqrt(abs(delta_bi)),
    deployment_id = factor(deployment_id)
  ) %>%
  filter(
    !is.na(delta_bi_signed_square_root), !is.na(previous_day_maximum_bi), !is.na(window_duration_hours),
    !is.na(minimum_temperature_c), !is.na(maximum_temperature_c), !is.na(temperature_at_previous_day_maximum_c),
    !is.na(maximum_wind_gust_m_s), !is.na(cumulative_sun_exposed_bi),
    !is.na(observation_order), !is.na(deployment_id)
  ) %>%
  arrange(deployment_id, observation_order)

thirty_random <- list(deployment_id = ~1, deployment_day_id = ~1)
thirty_correlation <- corAR1(form = ~ observation_order | deployment_day_id)
next_random <- list(deployment_id = ~1)
next_correlation <- corAR1(form = ~ observation_order | deployment_id)

frameworks <- list(
  thirty_minute_primary = list(
    data = thirty_minute_data, response = "delta_bi_signed_cuberoot",
    controls = "previous_bi + minutes_since_first_daily_observation", wind = "maximum_wind_gust_m_s",
    sun = "previous_sun_exposed_bi", temperatures = c(avg = "mean_temperature_c"),
    random = thirty_random, correlation = thirty_correlation,
    window = "thirty_minute", framework = "primary_controls"
  ),
  thirty_minute_no_previous = list(
    data = thirty_minute_data, response = "delta_bi_signed_cuberoot",
    controls = "minutes_since_first_daily_observation", wind = "maximum_wind_gust_m_s",
    sun = "previous_sun_exposed_bi", temperatures = c(avg = "mean_temperature_c"),
    random = thirty_random, correlation = thirty_correlation,
    window = "thirty_minute", framework = "sensitivity_no_previous_bi"
  ),
  thirty_minute_no_time = list(
    data = thirty_minute_data, response = "delta_bi_signed_cuberoot",
    controls = "previous_bi", wind = "maximum_wind_gust_m_s",
    sun = "previous_sun_exposed_bi", temperatures = c(avg = "mean_temperature_c"),
    random = thirty_random, correlation = thirty_correlation,
    window = "thirty_minute", framework = "sensitivity_no_time"
  ),
  next_day_primary = list(
    data = next_day_data, response = "delta_bi_signed_square_root",
    controls = "previous_day_maximum_bi + window_duration_hours", wind = "maximum_wind_gust_m_s",
    sun = "cumulative_sun_exposed_bi",
    temperatures = c(
      min = "minimum_temperature_c", max = "maximum_temperature_c",
      at_previous_max = "temperature_at_previous_day_maximum_c"
    ),
    random = next_random, correlation = next_correlation,
    window = "next_day", framework = "primary_previous_bi"
  ),
  next_day_no_previous = list(
    data = next_day_data, response = "delta_bi_signed_square_root",
    controls = "window_duration_hours", wind = "maximum_wind_gust_m_s",
    sun = "cumulative_sun_exposed_bi",
    temperatures = c(
      min = "minimum_temperature_c", max = "maximum_temperature_c",
      at_previous_max = "temperature_at_previous_day_maximum_c"
    ),
    random = next_random, correlation = next_correlation,
    window = "next_day", framework = "sensitivity_no_previous_bi"
  )
)

comparisons <- imap(frameworks, function(config, output_name) {
  specs <- build_candidate_specs(
    config$response, config$controls, config$wind, config$sun,
    config$temperatures, config$window
  )
  comparison <- compare_candidates(
    specs, config$response, config$data, config$random, config$correlation,
    config$window, config$framework
  )
  write_csv(comparison, file.path(out_dir, paste0(output_name, "_comparison.csv")))
  write_csv(
    comparison %>%
      filter(status == "success", is.finite(AICc)) %>%
      arrange(AICc) %>%
      select(
        rank_AICc, candidate_id, hypothesis, temperature_variant,
        legacy_model, mirror_of, AICc, delta_AICc, weight_AICc, formula
      ),
    file.path(out_dir, paste0(output_name, "_ranking.csv"))
  )
  comparison
})

selected_outputs <- imap(frameworks, function(config, output_name) {
  selected <- refit_selected(
    comparisons[[output_name]], config$data, config$random, config$correlation
  )
  write_csv(selected$summary, file.path(out_dir, paste0(output_name, "_selected_summary.csv")))
  selected
})

selected_models <- bind_rows(map(selected_outputs, "selected"))
selected_fit_statistics <- bind_rows(map(selected_outputs, "fit"))
write_csv(selected_models, file.path(out_dir, "selected_models.csv"))
write_csv(selected_fit_statistics, file.path(out_dir, "selected_model_fit_statistics.csv"))
write_csv(bind_rows(comparisons), file.path(out_dir, "all_comparisons.csv"))

figure_dir <- file.path(out_dir, "figures")
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

thirty_model <- selected_outputs$thirty_minute_primary$model$gam
thirty_lme <- selected_outputs$thirty_minute_primary$model$lme
temperature_values <- c(10, 15, 20)
sun_values <- c(0, 7, 20)
previous_bi_value <- median(thirty_minute_data$previous_bi)
time_value <- median(thirty_minute_data$minutes_since_first_daily_observation)
wind_max_plot <- unname(quantile(thirty_minute_data$maximum_wind_gust_m_s, 0.99))

fixed_beta <- fixef(thirty_lme)
fixed_vcov <- vcov(thirty_lme)
fixed_df <- min(summary(thirty_lme)$tTable[, "DF"])
conditional_wind_effect <- function(temperature, direct_sun) {
  contrast <- setNames(rep(0, length(fixed_beta)), names(fixed_beta))
  contrast["Xmaximum_wind_gust_m_s"] <- 1
  contrast["Xmaximum_wind_gust_m_s:mean_temperature_c"] <- temperature
  contrast["Xmaximum_wind_gust_m_s:previous_sun_exposed_bi"] <- direct_sun
  contrast["Xmaximum_wind_gust_m_s:mean_temperature_c:previous_sun_exposed_bi"] <-
    temperature * direct_sun
  estimate <- sum(contrast * fixed_beta)
  standard_error <- sqrt(as.numeric(t(contrast) %*% fixed_vcov %*% contrast))
  t_value <- estimate / standard_error
  tibble(
    temperature_c = temperature,
    sun_exposed_bi = direct_sun,
    wind_effect_per_1_ms = estimate,
    standard_error = standard_error,
    denominator_df = fixed_df,
    t_value = t_value,
    p_value = 2 * pt(abs(t_value), df = fixed_df, lower.tail = FALSE),
    conf_low = estimate + qt(0.025, df = fixed_df) * standard_error,
    conf_high = estimate + qt(0.975, df = fixed_df) * standard_error
  )
}

conditional_table <- bind_rows(lapply(temperature_values, function(temperature) {
  bind_rows(lapply(sun_values, function(sun) {
    conditional_wind_effect(temperature, sun)
  }))
}))
write_csv(
  conditional_table,
  file.path(out_dir, "thirty_minute_conditional_wind_effects.csv")
)

prediction_grid <- expand.grid(
  maximum_wind_gust_m_s = seq(0, wind_max_plot, length.out = 240),
  mean_temperature_c = temperature_values,
  previous_sun_exposed_bi = sun_values,
  KEEP.OUT.ATTRS = FALSE
) %>%
  as_tibble() %>%
  mutate(
    previous_bi = previous_bi_value,
    minutes_since_first_daily_observation = time_value
  )

prediction <- predict(thirty_model, newdata = prediction_grid, se.fit = TRUE)
prediction_grid <- prediction_grid %>%
  mutate(
    fit = as.numeric(prediction$fit),
    standard_error = as.numeric(prediction$se.fit),
    conf_low = fit - 1.96 * standard_error,
    conf_high = fit + 1.96 * standard_error,
    temperature_label = factor(
      mean_temperature_c,
      levels = temperature_values,
      labels = c("10 °C", "15 °C", "20 °C")
    ),
    direct_sun_label = factor(
      previous_sun_exposed_bi,
      levels = sun_values,
      labels = as.character(sun_values)
    )
  )
write_csv(prediction_grid, file.path(out_dir, "thirty_minute_figure_predictions.csv"))

sun_colors <- c("0" = "#4d4d4d", "7" = "#2b83ba", "20" = "#d7191c")
response_plot <- ggplot(
  prediction_grid,
  aes(
    x = maximum_wind_gust_m_s, y = fit, color = direct_sun_label,
    fill = direct_sun_label, group = direct_sun_label
  )
) +
  geom_ribbon(
    aes(ymin = conf_low, ymax = conf_high),
    alpha = 0.10, linewidth = 0, color = NA
  ) +
  geom_line(linewidth = 1.0) +
  geom_hline(yintercept = 0, color = "gray55", linewidth = 0.5) +
  facet_wrap(~temperature_label, nrow = 1) +
  scale_color_manual(values = sun_colors, name = "Sun-exposed BI") +
  scale_fill_manual(values = sun_colors, name = "Sun-exposed BI") +
  scale_x_continuous(
    limits = c(0, wind_max_plot), breaks = 0:6,
    expand = expansion(mult = 0.01)
  ) +
  labs(
    x = "Maximum wind gust (m/s)",
    y = "Predicted 30-minute ΔBI\n(signed cube-root scale)"
  ) +
  theme_like_reference(12, 0.98, reference = manuscript_figure_style) +
  theme(
    legend.position = "bottom",
    legend.title = element_text(
      size = reference_sizes(12, 0.98, manuscript_figure_style)$legend_title
    ),
    strip.text = element_text(
      color = "black", size = reference_sizes(12, 0.98, manuscript_figure_style)$axis_text
    ),
    panel.spacing.x = grid::unit(1, "lines")
  )

ggsave(
  file.path(figure_dir, "thirty_minute_predicted_response.png"),
  response_plot, width = 12, height = 5.8, dpi = 600, bg = "white"
)

message("Wrote harmonized comparisons to ", out_dir)
