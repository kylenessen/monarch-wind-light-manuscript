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

# Reconstruct the original candidate search. The source defines M1-M72 and
# M77-M78. M73-M76 are not defined candidates and are not invented here.
k_baseline <- 5
k_lag <- 5
weather_predictors <- c(
  "temp_min", "temp_max", "temp_at_max_count_t_1",
  "wind_max_gust", "sum_butterflies_direct_sun"
)
random_structure <- list(deployment_id = ~1)
correlation_structure <- corAR1(form = ~ observation_order_t | deployment_id)
model_specs <- list()
model_descriptions <- list()
add_candidate <- function(id, formula_str, description) {
  if (id <= 72 || id >= 77) {
    model_specs[[paste0("M", id)]] <<- formula_str
    model_descriptions[[paste0("M", id)]] <<- description
  }
}
smooth_base <- "s(max_butterflies_t_1, k = 5, bs = \"ts\") + s(lag_duration_hours, k = 5, bs = \"ts\")"
linear_base <- "max_butterflies_t_1 + lag_duration_hours"
model_num <- 1
add_candidate(model_num, paste("butterfly_diff_sqrt ~", smooth_base), "Null (smooth baseline)")
model_num <- model_num + 1
add_candidate(model_num, paste("butterfly_diff_sqrt ~", linear_base), "Null (linear baseline)")
model_num <- model_num + 1

for (pred in weather_predictors) {
  add_candidate(model_num, paste("butterfly_diff_sqrt ~", smooth_base, "+ s(", pred, ")"),
                paste0("Single: ", pred, " (smooth)"))
  model_num <- model_num + 1
  add_candidate(model_num, paste("butterfly_diff_sqrt ~", linear_base, "+ s(", pred, ")"),
                paste0("Single: ", pred, " (linear)"))
  model_num <- model_num + 1
}

interaction_pairs <- combn(weather_predictors, 2, simplify = FALSE)
for (pair in interaction_pairs) {
  pair_term <- paste0("ti(", pair[1], ", ", pair[2], ")")
  add_candidate(model_num, paste("butterfly_diff_sqrt ~", smooth_base, "+", pair_term),
                paste0("Interaction: ", pair[1], " x ", pair[2], " (smooth)"))
  model_num <- model_num + 1
  add_candidate(model_num, paste("butterfly_diff_sqrt ~", linear_base, "+", pair_term),
                paste0("Interaction: ", pair[1], " x ", pair[2], " (linear)"))
  model_num <- model_num + 1
}

for (pair in interaction_pairs) {
  pair_main <- paste0("s(", pair[1], ") + s(", pair[2], ") + ti(", pair[1], ", ", pair[2], ")")
  add_candidate(model_num, paste("butterfly_diff_sqrt ~", smooth_base, "+", pair_main),
                paste0("Additive + Interaction: ", pair[1], " + ", pair[2], " + ", pair[1], " x ", pair[2], " (smooth)"))
  model_num <- model_num + 1
  add_candidate(model_num, paste("butterfly_diff_sqrt ~", linear_base, "+", pair_main),
                paste0("Additive + Interaction: ", pair[1], " + ", pair[2], " + ", pair[1], " x ", pair[2], " (linear)"))
  model_num <- model_num + 1
}

additive_combos <- list(
  list(preds = c("temp_min", "temp_max", "temp_at_max_count_t_1"), desc = "All temperature"),
  list(preds = c("temp_min", "temp_max"), desc = "temp_min + temp_max"),
  list(preds = c("temp_min", "wind_max_gust"), desc = "temp_min + wind_max_gust"),
  list(preds = c("temp_max", "wind_max_gust"), desc = "temp_max + wind_max_gust"),
  list(preds = c("temp_at_max_count_t_1", "wind_max_gust"), desc = "temp_at_max_count_t_1 + wind_max_gust"),
  list(preds = c("temp_min", "temp_max", "temp_at_max_count_t_1", "wind_max_gust"), desc = "All temp + wind"),
  list(preds = weather_predictors, desc = "All predictors (additive)")
)
for (combo in additive_combos) {
  preds_str <- paste0("s(", combo$preds, ")", collapse = " + ")
  add_candidate(model_num, paste("butterfly_diff_sqrt ~", smooth_base, "+", preds_str),
                paste0("Additive: ", combo$desc, " (smooth)"))
  model_num <- model_num + 1
  add_candidate(model_num, paste("butterfly_diff_sqrt ~", linear_base, "+", preds_str),
                paste0("Additive: ", combo$desc, " (linear)"))
  model_num <- model_num + 1
}

temp_preds <- c("temp_min", "temp_max", "temp_at_max_count_t_1")
temp_pairs <- combn(temp_preds, 2, simplify = FALSE)
temp_main <- paste0("s(", temp_preds, ")", collapse = " + ")
temp_interactions <- paste0("ti(", vapply(temp_pairs, `[[`, character(1), 1), ", ",
                            vapply(temp_pairs, `[[`, character(1), 2), ")", collapse = " + ")
add_candidate(model_num, paste("butterfly_diff_sqrt ~", smooth_base, "+", temp_main, "+", temp_interactions),
              "All temp + all temp interactions (smooth)")
model_num <- model_num + 1
add_candidate(model_num, paste("butterfly_diff_sqrt ~", linear_base, "+", temp_main, "+", temp_interactions),
              "All temp + all temp interactions (linear)")
model_num <- model_num + 1
temp_wind_interactions <- paste0("ti(", temp_preds, ", wind_max_gust)", collapse = " + ")
all_main <- paste0("s(", weather_predictors, ")", collapse = " + ")
add_candidate(model_num, paste("butterfly_diff_sqrt ~", smooth_base, "+", all_main, "+", temp_wind_interactions),
              "All additive + all temp x wind interactions (smooth)")
model_num <- model_num + 1
add_candidate(model_num, paste("butterfly_diff_sqrt ~", linear_base, "+", all_main, "+", temp_wind_interactions),
              "All additive + all temp x wind interactions (linear)")
model_num <- model_num + 1
all_interactions <- paste0("ti(", vapply(interaction_pairs, `[[`, character(1), 1), ", ",
                           vapply(interaction_pairs, `[[`, character(1), 2), ")", collapse = " + ")
add_candidate(model_num, paste("butterfly_diff_sqrt ~", smooth_base, "+", all_main, "+", all_interactions),
              "FULL MODEL: All terms + all interactions (smooth)")
model_num <- model_num + 1
add_candidate(model_num, paste("butterfly_diff_sqrt ~", linear_base, "+", all_main, "+", all_interactions),
              "FULL MODEL: All terms + all interactions (linear)")

add_candidate(77,
  paste("butterfly_diff_sqrt ~", smooth_base, "+ wind_max_gust + sum_butterflies_direct_sun + wind_max_gust:sum_butterflies_direct_sun"),
  "Linear interaction: wind_max_gust x sum_butterflies_direct_sun (with baseline + lag duration)")
add_candidate(78,
  paste("butterfly_diff_sqrt ~", smooth_base, "+ temp_min + temp_max + wind_max_gust + sum_butterflies_direct_sun + wind_max_gust:sum_butterflies_direct_sun"),
  "Linear interaction + temp_min + temp_max (with baseline + lag duration)")

stopifnot(length(model_specs) == 74, identical(names(model_specs), c(paste0("M", 1:72), "M77", "M78")))

fit_model_safe <- function(formula_str, method = "ML") {
  warnings <- character()
  tryCatch({
    model <- withCallingHandlers(
      gamm(
        as.formula(formula_str), data = data,
        random = random_structure,
        correlation = correlation_structure,
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

fit_results <- lapply(model_specs, fit_model_safe, method = "ML")
names(fit_results) <- names(model_specs)
fits_ml <- lapply(fit_results, `[[`, "model")
names(fits_ml) <- names(model_specs)
fit_errors <- vapply(fit_results, `[[`, character(1), "error")
fit_warnings <- vapply(fit_results, `[[`, character(1), "warning")
has_convergence_warning <- grepl("convergence", fit_warnings, ignore.case = TRUE)
names(has_convergence_warning) <- names(model_specs)

model_rows <- lapply(names(model_specs), function(id) {
  fit <- fits_ml[[id]]
  if (is.null(fit) || is.null(fit$lme) || has_convergence_warning[[id]]) {
    status <- if (has_convergence_warning[[id]]) "convergence_failure" else "failure"
    return(tibble(
      model = id, description = model_descriptions[[id]], formula = model_specs[[id]],
      status = status, error = fit_errors[[id]], warning = fit_warnings[[id]], n = nrow(data),
      likelihood_method = "ML", AIC = NA_real_, BIC = NA_real_, logLik = NA_real_,
      df = NA_real_, AICc = NA_real_, delta_AICc = NA_real_, weight_AICc = NA_real_
    ))
  }
  loglik_val <- tryCatch(as.numeric(logLik(fit$lme)), error = function(e) NA_real_)
  df_val <- tryCatch(as.numeric(attr(logLik(fit$lme), "df")), error = function(e) NA_real_)
  n_val <- tryCatch(as.integer(nobs(fit$lme)), error = function(e) nrow(data))
  aic_val <- tryCatch(AIC(fit$lme), error = function(e) NA_real_)
  bic_val <- tryCatch(BIC(fit$lme), error = function(e) NA_real_)
  aicc_val <- if (is.finite(aic_val) && is.finite(df_val) && n_val > df_val + 1) {
    aic_val + (2 * df_val * (df_val + 1)) / (n_val - df_val - 1)
  } else NA_real_
  tibble(
    model = id, description = model_descriptions[[id]], formula = model_specs[[id]],
    status = "success", error = "", warning = fit_warnings[[id]], n = n_val, likelihood_method = "ML",
    AIC = aic_val, BIC = bic_val, logLik = loglik_val, df = df_val,
    AICc = aicc_val, delta_AICc = NA_real_, weight_AICc = NA_real_
  )
})
model_table <- bind_rows(model_rows)
rankable <- model_table$status == "success" & is.finite(model_table$AICc)
if (!any(rankable)) {
  stop("No Next Day candidate model produced a finite ML AICc value.")
}
min_aicc <- min(model_table$AICc[rankable])
model_table$delta_AICc[rankable] <- model_table$AICc[rankable] - min_aicc
model_table$weight_AICc[rankable] <- exp(-0.5 * model_table$delta_AICc[rankable]) /
  sum(exp(-0.5 * model_table$delta_AICc[rankable]))
write_csv(model_table, file.path(out_dir, "model_comparison_comprehensive.csv"))
ranked_models <- model_table %>% filter(status == "success", is.finite(AICc)) %>% arrange(delta_AICc)
selected_id <- ranked_models$model[1]
selected_reml <- fit_model_safe(model_specs[[selected_id]], method = "REML")
if (is.null(selected_reml$model) || is.null(selected_reml$model$lme) ||
    grepl("convergence", selected_reml$warning, ignore.case = TRUE)) {
  stop("Selected model REML refit failed: ", selected_reml$error,
       selected_reml$warning)
}
model <- selected_reml$model
fits <- fits_ml
fits[[selected_id]] <- model

top5 <- model_table %>%
  filter(status == "success") %>%
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
  model = selected_id,
  n = nrow(data),
  adjusted_r_squared = model_summary$r.sq,
  scale = model_summary$scale,
  formula = model_specs[[selected_id]]
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
  xlab = "Maximum wind gust (m/s)",
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
