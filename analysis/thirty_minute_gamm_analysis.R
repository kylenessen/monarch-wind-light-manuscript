#!/usr/bin/env Rscript

# Reproducible 30-minute GAMM candidate comparison and selected-model export.

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(mgcv)
  library(nlme)
  library(purrr)
  library(readr)
  library(gratia)
  library(patchwork)
  library(tibble)
  library(knitr)
  library(here)
  library(glue)
})

source(here("analysis", "lib", "manuscript_figure_style.R"))

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
export_dir <- here("analysis", "outputs", "30_minute")
fig_dir <- file.path(export_dir, "figures")
tab_dir <- file.path(export_dir, "tables")
text_dir <- file.path(export_dir, "text")
for (d in c(export_dir, fig_dir, tab_dir, text_dir)) if (!dir.exists(d)) dir.create(d, recursive = TRUE)

# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
data_file <- here("data", "monarch_analysis_lag30min.csv")
stopifnot(file.exists(data_file))
dat <- readr::read_csv(data_file, show_col_types = FALSE)

# Prepare modeling data
model_data <- dat %>%
  filter(
    !is.na(butterfly_difference_cbrt),
    !is.na(total_butterflies_t_lag),
    !is.na(temperature_avg),
    !is.na(max_gust),
    !is.na(butterflies_direct_sun_t_lag),
    !is.na(observation_order_within_day_t),
    !is.na(deployment_day),
    !is.na(deployment_id)
  )

n_obs <- nrow(model_data)
n_periods <- dplyr::n_distinct(model_data$deployment_day)
n_sites <- if ("grove" %in% names(model_data)) dplyr::n_distinct(model_data$grove) else dplyr::n_distinct(model_data$deployment_id)

# ----------------------------------------------------------------------------
# Model set. M20 and M44 are exact duplicates of M17 and M41.
# They are excluded without renumbering so the original candidate IDs remain
# traceable to the exploratory analysis.
# ----------------------------------------------------------------------------
random_structure <- list(deployment_id = ~1, deployment_day = ~1)
correlation_structure <- corAR1(form = ~ observation_order_within_day_t | deployment_day)

model_specs <- list(
  # Baseline
  "M1"  = "butterfly_difference_cbrt ~ total_butterflies_t_lag",

  # Main effects (with lag)
  "M2"  = "butterfly_difference_cbrt ~ total_butterflies_t_lag + max_gust",
  "M3"  = "butterfly_difference_cbrt ~ total_butterflies_t_lag + temperature_avg",
  "M4"  = "butterfly_difference_cbrt ~ total_butterflies_t_lag + butterflies_direct_sun_t_lag",

  # Two vars (with lag)
  "M5"  = "butterfly_difference_cbrt ~ total_butterflies_t_lag + max_gust + temperature_avg",
  "M6"  = "butterfly_difference_cbrt ~ total_butterflies_t_lag + max_gust + butterflies_direct_sun_t_lag",
  "M7"  = "butterfly_difference_cbrt ~ total_butterflies_t_lag + temperature_avg + butterflies_direct_sun_t_lag",

  # Three vars main effects (with lag)
  "M8"  = "butterfly_difference_cbrt ~ total_butterflies_t_lag + max_gust + temperature_avg + butterflies_direct_sun_t_lag",

  # Interactions (with lag)
  "M9"  = "butterfly_difference_cbrt ~ total_butterflies_t_lag + max_gust * temperature_avg",
  "M10" = "butterfly_difference_cbrt ~ total_butterflies_t_lag + max_gust * butterflies_direct_sun_t_lag",
  "M11" = "butterfly_difference_cbrt ~ total_butterflies_t_lag + temperature_avg * butterflies_direct_sun_t_lag",
  "M12" = "butterfly_difference_cbrt ~ total_butterflies_t_lag + max_gust * temperature_avg + butterflies_direct_sun_t_lag",
  "M13" = "butterfly_difference_cbrt ~ total_butterflies_t_lag + max_gust * butterflies_direct_sun_t_lag + temperature_avg",
  "M14" = "butterfly_difference_cbrt ~ total_butterflies_t_lag + temperature_avg * butterflies_direct_sun_t_lag + max_gust",
  "M15" = "butterfly_difference_cbrt ~ total_butterflies_t_lag + max_gust * temperature_avg + max_gust * butterflies_direct_sun_t_lag + temperature_avg * butterflies_direct_sun_t_lag",
  "M16" = "butterfly_difference_cbrt ~ total_butterflies_t_lag + max_gust * temperature_avg * butterflies_direct_sun_t_lag",

  # Smooth (with lag)
  "M17" = "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + s(temperature_avg) + s(butterflies_direct_sun_t_lag)",
  "M18" = "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + temperature_avg + s(butterflies_direct_sun_t_lag)",
  "M19" = "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + s(max_gust) + temperature_avg + s(butterflies_direct_sun_t_lag)",
  "M20" = "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + s(temperature_avg) + s(butterflies_direct_sun_t_lag)",
  "M21" = "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + s(max_gust) + s(temperature_avg) + s(butterflies_direct_sun_t_lag)",
  "M22" = "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + temperature_avg + s(butterflies_direct_sun_t_lag) + s(time_within_day_t)",
  "M23" = "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + s(temperature_avg) + s(butterflies_direct_sun_t_lag) + s(time_within_day_t)",
  "M24" = "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + s(max_gust) + s(temperature_avg) + s(butterflies_direct_sun_t_lag) + s(time_within_day_t)",

  # Absolute-change framework (no lag)
  "M25" = "butterfly_difference_cbrt ~ 1",
  "M26" = "butterfly_difference_cbrt ~ max_gust",
  "M27" = "butterfly_difference_cbrt ~ temperature_avg",
  "M28" = "butterfly_difference_cbrt ~ butterflies_direct_sun_t_lag",
  "M29" = "butterfly_difference_cbrt ~ max_gust + temperature_avg",
  "M30" = "butterfly_difference_cbrt ~ max_gust + butterflies_direct_sun_t_lag",
  "M31" = "butterfly_difference_cbrt ~ temperature_avg + butterflies_direct_sun_t_lag",
  "M32" = "butterfly_difference_cbrt ~ max_gust + temperature_avg + butterflies_direct_sun_t_lag",
  "M33" = "butterfly_difference_cbrt ~ max_gust * temperature_avg",
  "M34" = "butterfly_difference_cbrt ~ max_gust * butterflies_direct_sun_t_lag",
  "M35" = "butterfly_difference_cbrt ~ temperature_avg * butterflies_direct_sun_t_lag",
  "M36" = "butterfly_difference_cbrt ~ max_gust * temperature_avg + butterflies_direct_sun_t_lag",
  "M37" = "butterfly_difference_cbrt ~ max_gust * butterflies_direct_sun_t_lag + temperature_avg",
  "M38" = "butterfly_difference_cbrt ~ temperature_avg * butterflies_direct_sun_t_lag + max_gust",
  "M39" = "butterfly_difference_cbrt ~ max_gust * temperature_avg + max_gust * butterflies_direct_sun_t_lag + temperature_avg * butterflies_direct_sun_t_lag",
  "M40" = "butterfly_difference_cbrt ~ max_gust * temperature_avg * butterflies_direct_sun_t_lag",

  # Smooths (no lag)
  "M41" = "butterfly_difference_cbrt ~ s(temperature_avg) + s(butterflies_direct_sun_t_lag)",
  "M42" = "butterfly_difference_cbrt ~ temperature_avg + s(butterflies_direct_sun_t_lag)",
  "M43" = "butterfly_difference_cbrt ~ s(max_gust) + temperature_avg + s(butterflies_direct_sun_t_lag)",
  "M44" = "butterfly_difference_cbrt ~ s(temperature_avg) + s(butterflies_direct_sun_t_lag)",
  "M45" = "butterfly_difference_cbrt ~ s(max_gust) + s(temperature_avg) + s(butterflies_direct_sun_t_lag)",
  "M46" = "butterfly_difference_cbrt ~ temperature_avg + s(butterflies_direct_sun_t_lag) + s(time_within_day_t)",
  "M47" = "butterfly_difference_cbrt ~ s(temperature_avg) + s(butterflies_direct_sun_t_lag) + s(time_within_day_t)",
  "M48" = "butterfly_difference_cbrt ~ s(max_gust) + s(temperature_avg) + s(butterflies_direct_sun_t_lag) + s(time_within_day_t)"
)

# Add tensor-product interaction candidates (wind x sun)
model_specs <- c(model_specs, list(
  # With lag term and diurnal controls
  "M49" = "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + ti(max_gust, butterflies_direct_sun_t_lag)",
  "M50" = "butterfly_difference_cbrt ~ s(total_butterflies_t_lag) + s(temperature_avg) + s(time_within_day_t) + ti(max_gust, butterflies_direct_sun_t_lag)",
  # Without lag term (absolute change)
  "M51" = "butterfly_difference_cbrt ~ ti(max_gust, butterflies_direct_sun_t_lag)",
  "M52" = "butterfly_difference_cbrt ~ s(temperature_avg) + s(time_within_day_t) + ti(max_gust, butterflies_direct_sun_t_lag)"
))

model_specs <- model_specs[!names(model_specs) %in% c("M20", "M44")]

fit_model <- function(formula_str, data, method = "ML") {
  warnings <- character()
  tryCatch({
    model <- withCallingHandlers(
      gamm(as.formula(formula_str),
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
    list(model = model, error = "", warning = paste(unique(warnings), collapse = " | "))
  }, error = function(e) {
    list(model = NULL, error = conditionMessage(e), warning = paste(unique(warnings), collapse = " | "))
  })
}

cat(sprintf("Fitting %d candidate models...\n", length(model_specs)))
fit_results <- lapply(model_specs, fit_model, data = model_data, method = "ML")
names(fit_results) <- names(model_specs)
fits_ml <- lapply(fit_results, `[[`, "model")
names(fits_ml) <- names(model_specs)
fit_error <- vapply(fit_results, function(x) {
  x$error
}, character(1))
fit_warning <- vapply(fit_results, `[[`, character(1), "warning")
has_convergence_warning <- grepl("convergence", fit_warning, ignore.case = TRUE)
names(has_convergence_warning) <- names(model_specs)
ok <- vapply(fits_ml, function(x) !is.null(x) && !is.null(x$lme), logical(1)) &
  !has_convergence_warning
cat(sprintf("%d models fitted successfully. %d failed.\n", sum(ok), sum(!ok)))

# ----------------------------------------------------------------------------
# AIC ranking + helper utilities
# ----------------------------------------------------------------------------
aic_tbl <- purrr::map_dfr(names(model_specs), function(nm) {
  m <- fits_ml[[nm]]
  if (!ok[[nm]]) return(NULL)
  aic_val <- tryCatch(AIC(m$lme), error = function(e) NA_real_)
  loglik_val <- tryCatch(as.numeric(logLik(m$lme)), error = function(e) NA_real_)
  df_val <- tryCatch(as.numeric(attr(logLik(m$lme), "df")), error = function(e) NA_real_)
  if (!is.finite(aic_val) || !is.finite(loglik_val) || !is.finite(df_val)) return(NULL)
  tibble(Model = nm, Formula = model_specs[[nm]], AIC = aic_val,
         LogLik = loglik_val, df = df_val, Likelihood_Method = "ML")
}) %>%
  arrange(.data$AIC) %>%
  mutate(
    Delta_AIC = .data$AIC - min(.data$AIC),
    Weight = exp(-0.5 * .data$Delta_AIC) / sum(exp(-0.5 * .data$Delta_AIC))
  )

best_id <- aic_tbl$Model[1]
if (length(best_id) == 0 || is.na(best_id)) {
  stop("No 30-minute candidate model produced a finite ML AIC value.")
}
best_reml_result <- fit_model(model_specs[[best_id]], model_data, method = "REML")
if (is.null(best_reml_result$model) || is.null(best_reml_result$model$lme) ||
    grepl("convergence", best_reml_result$warning, ignore.case = TRUE)) {
  stop("Selected model REML refit failed: ", best_reml_result$error,
       best_reml_result$warning)
}
best <- best_reml_result$model
fits <- fits_ml
fits[[best_id]] <- best

audit_tbl <- purrr::map_dfr(names(model_specs), function(nm) {
  m <- fits_ml[[nm]]
  if (!ok[[nm]]) {
    status <- if (has_convergence_warning[[nm]]) "convergence_failure" else "failure"
    return(tibble(
      Model = nm, Formula = model_specs[[nm]], Status = status,
      Error = fit_error[[nm]], Warning = fit_warning[[nm]], n = nrow(model_data),
      Likelihood_Method = "ML", LogLik = NA_real_, df = NA_real_,
      AIC = NA_real_, Delta_AIC = NA_real_, Weight = NA_real_
    ))
  }
  loglik_val <- tryCatch(as.numeric(logLik(m$lme)), error = function(e) NA_real_)
  df_val <- tryCatch(as.numeric(attr(logLik(m$lme), "df")), error = function(e) NA_real_)
  aic_val <- tryCatch(AIC(m$lme), error = function(e) NA_real_)
  tibble(
    Model = nm, Formula = model_specs[[nm]], Status = "success", Error = "",
    Warning = fit_warning[[nm]],
    n = nrow(model_data), Likelihood_Method = "ML", LogLik = loglik_val,
    df = df_val, AIC = aic_val, Delta_AIC = NA_real_, Weight = NA_real_
  )
})
audit_ok <- audit_tbl$Status == "success" & is.finite(audit_tbl$AIC)
audit_min <- min(audit_tbl$AIC[audit_ok])
audit_tbl$Delta_AIC[audit_ok] <- audit_tbl$AIC[audit_ok] - audit_min
audit_tbl$Weight[audit_ok] <- exp(-0.5 * audit_tbl$Delta_AIC[audit_ok]) /
  sum(exp(-0.5 * audit_tbl$Delta_AIC[audit_ok]))
readr::write_csv(audit_tbl, file.path(export_dir, "model_audit_30min.csv"))

# Helper to get a nice, human-readable term list from a formula
humanize <- function(x) {
  dplyr::case_when(
    x == "total_butterflies_t_lag" ~ "Previous butterfly count",
    x == "max_gust" ~ "Maximum wind speed",
    x == "temperature_avg" ~ "Temperature",
    x == "butterflies_direct_sun_t_lag" ~ "Butterflies in direct sun",
    x == "time_within_day_t" ~ "Time since sunrise",
    TRUE ~ x
  )
}

readable_terms <- function(formula_str) {
  rhs <- gsub("^butterfly_difference_cbrt ~ ", "", formula_str)
  # split on + and remove whitespace
  terms <- trimws(strsplit(rhs, "+", fixed = TRUE)[[1]])
  terms <- terms[terms != ""]
  term_list <- vapply(terms, function(t) {
    if (startsWith(t, "s(") && endsWith(t, ")")) {
      inner <- substr(t, 3, nchar(t) - 1)
      humanize(inner)
    } else if (startsWith(t, "ti(") && endsWith(t, ")")) {
      inner <- substr(t, 4, nchar(t) - 1)
      parts <- trimws(strsplit(inner, ",", fixed = TRUE)[[1]])
      paste0("Interaction (tensor): ", paste(humanize(parts), collapse = ", "))
    } else if (grepl("*", t, fixed = TRUE)) {
      parts <- trimws(strsplit(t, "*", fixed = TRUE)[[1]])
      paste0("Interaction: ", paste(humanize(parts), collapse = " x "))
    } else {
      paste0(humanize(t), " (linear)")
    }
  }, character(1))
  paste(term_list, collapse = ", ")
}

# ----------------------------------------------------------------------------
# Request 2: Top 5 table (LaTeX)
# ----------------------------------------------------------------------------
top5 <- aic_tbl %>%
  slice(1:5) %>%
  mutate(
    Terms = purrr::map_chr(Formula, readable_terms),
    AIC = round(AIC, 3), Delta_AIC = round(Delta_AIC, 3), Weight = round(Weight, 4)
  )

# Extract p-value for wind if present (linear or smooth)
get_wind_p <- function(gamm_fit) {
  st <- summary(gamm_fit$gam)
  # linear term
  if ("max_gust" %in% rownames(st$p.table)) {
    return(st$p.table["max_gust", "Pr(>|t|)"])
  }
  # smooth term
  sm <- st$s.table
  r <- grep("max_gust", rownames(sm))
  if (length(r)) {
    return(sm[r[1], "p-value"])
  } else {
    return(NA_real_)
  }
}

top5$Wind_p <- purrr::map_dbl(top5$Model, ~ get_wind_p(fits[[.x]]))
top5$Wind_p <- ifelse(is.na(top5$Wind_p), NA, signif(top5$Wind_p, 3))

top5_out <- top5 %>%
  select(Model, Terms, AIC, Delta_AIC, Weight, Wind_p)

top5_tex <- kable(top5_out,
  format = "latex", booktabs = TRUE, escape = FALSE,
  caption = "Top 5 models ranked by AIC (30-minute analysis)"
)
writeLines(top5_tex, file.path(tab_dir, "model_selection_30min.tex"))
readr::write_csv(top5_out, file.path(tab_dir, "model_selection_30min.csv"))
readr::write_csv(top5_out, file.path(export_dir, "model_selection_30min.csv"))

# ----------------------------------------------------------------------------
# Request 1 & 3: Best model summary paragraph + equation
# ----------------------------------------------------------------------------
best_row <- top5_out[1, ]
next_best <- aic_tbl %>% slice(2)

# Which top models include a smooth predictor for wind alone?
top_models <- aic_tbl %>% slice(1:5)
includes_wind_smooth <- vapply(top_models$Model, function(id) {
  st <- rownames(summary(fits[[id]]$gam)$s.table)
  any(grepl("s\\(max_gust\\)", st))
}, logical(1))

best_weight <- aic_tbl$Weight[1]
delta_next <- round(next_best$Delta_AIC, 1)

para <- glue::glue(
  "The 30-minute analysis used {n_obs} paired observations from {n_periods} monitoring periods at {n_sites} overwintering site{ifelse(n_sites==1,'','s')} during the 2023-2024 season. ",
  "We compared {length(model_specs)} unique candidate models using maximum likelihood. ",
  "Of these, {nrow(aic_tbl)} produced rankable fits. Model {best_id} ranked first and included {readable_terms(model_specs[[best_id]])}. ",
  "It had an AIC of {format(round(aic_tbl$AIC[1], 3), nsmall = 3)}, an Akaike weight of {format(round(best_weight, 4), nsmall = 4)}, and a Delta AIC of {delta_next} relative to the next-ranked model. ",
  "Model {best_id} was then refitted using restricted maximum likelihood for coefficient estimation."
)

writeLines(as.character(para), file.path(text_dir, "paragraph.md"))

# Best model equation (plain)
eq_plain <- paste(
  aic_tbl$Formula[1],
  "+ random(deployment_id, deployment_day) + AR1(within deployment_day)"
)
writeLines(eq_plain, file.path(text_dir, "best_model_equation.txt"))
writeLines(best_id, file.path(text_dir, "best_model_id.txt"))

# ----------------------------------------------------------------------------
# Request 4: GAM basis dimension check (gam.check)
# ----------------------------------------------------------------------------
check_output <- capture.output(gam.check(best$gam, rep = 500))
writeLines(check_output, file.path(text_dir, "gam_check_output.txt"))

# Get smooth terms table for later use
sm <- summary(best$gam)$s.table
parametric_terms <- as.data.frame(summary(best$gam)$p.table) %>%
  tibble::rownames_to_column("term") %>%
  tibble::as_tibble() %>%
  mutate(term_type = "parametric")
smooth_terms <- as.data.frame(sm) %>%
  tibble::rownames_to_column("term") %>%
  tibble::as_tibble() %>%
  mutate(term_type = "smooth")
readr::write_csv(
  bind_rows(parametric_terms, smooth_terms),
  file.path(tab_dir, "selected_model_summary.csv")
)
readr::write_csv(tibble(
  model = best_id,
  n = n_obs,
  adjusted_r_squared = summary(best$gam)$r.sq,
  scale = summary(best$gam)$scale,
  formula = model_specs[[best_id]]
), file.path(tab_dir, "selected_model_fit_statistics.csv"))

# ----------------------------------------------------------------------------
# Bivariate plot: wind speed vs Delta BI
# ----------------------------------------------------------------------------
cat("Creating bivariate plot: wind speed vs Delta BI...\n")

# Calculate correlation
wind_corr <- cor(model_data$max_gust, model_data$butterfly_difference_cbrt,
                 use = "complete.obs")

# Fit linear model for trend line
lm_wind <- lm(butterfly_difference_cbrt ~ max_gust, data = model_data)
r_squared <- summary(lm_wind)$r.squared

cat(sprintf("Wind vs change correlation: r = %.2f, R² = %.4f\n", wind_corr, r_squared))

# Define custom_theme early for bivariate plot
custom_theme <- theme_minimal(base_size = 12) + theme(
  panel.grid.major = element_line(color = "gray90", linewidth = 0.5),
  panel.grid.minor = element_line(color = "gray95", linewidth = 0.3),
  axis.text = element_text(color = "black"),
  axis.title = element_text(color = "black", face = "bold"),
  plot.title = element_blank()
)

p_wind_bivariate <- ggplot(model_data, aes(x = max_gust, y = butterfly_difference_cbrt)) +
  geom_jitter(alpha = 0.5, size = 2, color = "#4d4d4d", width = 0.1, height = 0) +
  geom_vline(xintercept = 2, color = "red", linetype = "dashed", linewidth = 0.6) +
  geom_hline(yintercept = 0, color = "gray65", linewidth = 0.5) +
  scale_x_continuous(limits = c(0, NA), expand = expansion(mult = c(0, 0.05))) +
  labs(
    x = "Maximum wind speed (m/s)",
    y = "Delta BI (cube root transformed)",
    title = sprintf("Maximum wind speed vs Delta BI\nCorrelation: r = %.2f", wind_corr)
  ) +
  custom_theme +
  theme(plot.title = element_text(size = 14, hjust = 0, face = "plain"))

ggsave(file.path(fig_dir, "wind_vs_change_bivariate.png"), p_wind_bivariate,
       width = 7, height = 6, dpi = 300, bg = "white")
cat("Saved: wind_vs_change_bivariate.png\n\n")

# Untransformed version
wind_corr_raw <- cor(model_data$max_gust, model_data$butterfly_difference,
                     use = "complete.obs")

# Fit linear model for untransformed data
lm_wind_raw <- lm(butterfly_difference ~ max_gust, data = model_data)
p_value_raw <- summary(lm_wind_raw)$p.value[2]  # p-value for the slope

cat(sprintf("Wind vs change correlation (untransformed): r = %.2f, p = %.4f\n", wind_corr_raw, p_value_raw))

# Create main scatter plot
p_main <- ggplot(model_data, aes(x = max_gust, y = butterfly_difference)) +
  geom_jitter(alpha = 0.5, size = 2, color = "#4d4d4d", width = 0.1, height = 0) +
  geom_smooth(method = "lm", se = TRUE, color = "steelblue", fill = "steelblue",
              alpha = 0.25, linewidth = 1) +
  geom_vline(xintercept = 2, color = "red", linetype = "dashed", linewidth = 0.8) +
  geom_hline(yintercept = 0, color = "gray65", linewidth = 0.5) +
  geom_rug(alpha = 0.3, length = unit(0.02, "npc")) +
  scale_x_continuous(limits = c(0, max(model_data$max_gust, na.rm = TRUE) * 1.05),
                     expand = c(0, 0)) +
  scale_y_continuous(limits = c(min(model_data$butterfly_difference, na.rm = TRUE) * 1.05,
                                max(model_data$butterfly_difference, na.rm = TRUE) * 1.05),
                     expand = c(0, 0)) +
  labs(
    x = "Maximum wind speed (m/s)",
    y = "Delta BI",
    title = sprintf("Wind Disruption (30 minute interval)\nr = %.2f, p = %.4f",
                   wind_corr_raw, p_value_raw)
  ) +
  custom_theme +
  theme(plot.title = element_text(size = 14, hjust = 0.5, face = "plain"),
        plot.margin = margin(5, 5, 5, 5))

# Top marginal density plot for x-axis
dens_x <- ggplot(model_data, aes(x = max_gust)) +
  geom_density(fill = "#4d4d4d", alpha = 0.4, color = "#4d4d4d", linewidth = 0.5) +
  scale_x_continuous(limits = c(0, max(model_data$max_gust, na.rm = TRUE) * 1.05),
                     expand = c(0, 0)) +
  theme_void() +
  theme(plot.margin = margin(0, 5, 0, 5))

# Right marginal density plot for y-axis
dens_y <- ggplot(model_data, aes(x = butterfly_difference)) +
  geom_density(fill = "#4d4d4d", alpha = 0.4, color = "#4d4d4d", linewidth = 0.5) +
  scale_x_continuous(limits = c(min(model_data$butterfly_difference, na.rm = TRUE) * 1.05,
                                max(model_data$butterfly_difference, na.rm = TRUE) * 1.05),
                     expand = c(0, 0)) +
  theme_void() +
  theme(plot.margin = margin(5, 0, 5, 0)) +
  coord_flip()

# Combine plots using patchwork
p_wind_bivariate_raw <- dens_x + plot_spacer() + p_main + dens_y +
  plot_layout(ncol = 2, nrow = 2, widths = c(4, 1), heights = c(1, 4))

# Save combined plot
ggsave(file.path(fig_dir, "wind_vs_change_bivariate_untransformed.png"),
       p_wind_bivariate_raw,
       width = 8, height = 7, dpi = 300, bg = "white")
cat("Saved: wind_vs_change_bivariate_untransformed.png\n\n")

# ----------------------------------------------------------------------------
# Request 5: Combined partial effects for best model (1x3)
# ----------------------------------------------------------------------------

# Styling helpers: subtle grid, no titles
# (custom_theme already defined above for bivariate plot)
custom_theme <- theme_minimal(base_size = 12) + theme(
  panel.grid.major = element_line(color = "gray90", linewidth = 0.5),
  panel.grid.minor = element_line(color = "gray95", linewidth = 0.3),
  axis.text = element_text(color = "black"),
  axis.title = element_text(color = "black", face = "bold"),
  plot.title = element_blank() # No titles
)
lighten_color <- function(hex, amount = 0.12) {
  rgbv <- col2rgb(hex)
  out <- rgbv + (255 - rgbv) * amount
  rgb(out[1], out[2], out[3], maxColorValue = 255)
}

# Colors inspired by the example
col_prev <- "#9673c5"
col_time <- "#79a44c"
col_temp <- "#b86e7e"
col_prev_l <- lighten_color(col_prev)
col_time_l <- lighten_color(col_time)
col_temp_l <- lighten_color(col_temp)

have_prev <- any(grepl("s\\(total_butterflies_t_lag\\)", rownames(sm)))
have_time <- any(grepl("s\\(time_within_day_t\\)", rownames(sm)))
have_temp <- any(grepl("s\\(temperature_avg\\)", rownames(sm)))

# First, collect all plots to determine y-axis limits
temp_plots <- list()
if (have_prev) {
  p_prev <- draw(best$gam, select = "s(total_butterflies_t_lag)", rug = FALSE, residuals = FALSE)
  temp_plots[[length(temp_plots) + 1]] <- p_prev
}
if (have_time) {
  p_time <- draw(best$gam, select = "s(time_within_day_t)", rug = FALSE, residuals = FALSE)
  temp_plots[[length(temp_plots) + 1]] <- p_time
}
if (have_temp) {
  p_temp <- draw(best$gam, select = "s(temperature_avg)", rug = FALSE, residuals = FALSE)
  temp_plots[[length(temp_plots) + 1]] <- p_temp
}

# Calculate common y-axis limits
y_min <- -Inf
y_max <- Inf
if (length(temp_plots) > 0) {
  y_ranges <- lapply(temp_plots, function(p) {
    build <- ggplot_build(p)
    c(min(build$data[[1]]$ymin, na.rm = TRUE), max(build$data[[1]]$ymax, na.rm = TRUE))
  })
  y_min <- min(sapply(y_ranges, "[", 1))
  y_max <- max(sapply(y_ranges, "[", 2))
  # Add some padding
  y_padding <- (y_max - y_min) * 0.1
  y_min <- y_min - y_padding
  y_max <- y_max + y_padding
}

plots <- list()
plot_index <- 0
# Count total plots to determine which is last
total_plots <- sum(have_prev, have_time, have_temp)

if (have_prev) {
  plot_index <- plot_index + 1
  # Only the first plot gets the y-axis label
  y_label <- if (plot_index == 1) "Partial effect" else ""
  # Only the last plot gets the caption
  caption_text <- if (plot_index == total_plots) "Basis: TPRS" else NULL

  p_prev <- draw(best$gam, select = "s(total_butterflies_t_lag)", rug = FALSE, residuals = FALSE) +
    labs(x = "Previous butterfly count", y = y_label, caption = caption_text) +
    custom_theme +
    coord_cartesian(ylim = c(y_min, y_max))

  # Color the confidence bands and lines
  for (i in seq_along(p_prev$layers)) {
    if ("colour" %in% names(p_prev$layers[[i]]$aes_params)) p_prev$layers[[i]]$aes_params$colour <- col_prev
    if ("fill" %in% names(p_prev$layers[[i]]$aes_params)) p_prev$layers[[i]]$aes_params$fill <- col_prev_l
  }
  plots[[length(plots) + 1]] <- p_prev
}

if (have_time) {
  plot_index <- plot_index + 1
  # Only the first plot gets the y-axis label
  y_label <- if (plot_index == 1) "Partial effect" else ""
  # Only the last plot gets the caption
  caption_text <- if (plot_index == total_plots) "Basis: TPRS" else NULL

  p_time <- draw(best$gam, select = "s(time_within_day_t)", rug = FALSE, residuals = FALSE) +
    labs(x = "Time since sunrise (minutes)", y = y_label, caption = caption_text) +
    custom_theme +
    coord_cartesian(ylim = c(y_min, y_max))

  for (i in seq_along(p_time$layers)) {
    if ("colour" %in% names(p_time$layers[[i]]$aes_params)) p_time$layers[[i]]$aes_params$colour <- col_time
    if ("fill" %in% names(p_time$layers[[i]]$aes_params)) p_time$layers[[i]]$aes_params$fill <- col_time_l
  }
  plots[[length(plots) + 1]] <- p_time
}

if (have_temp) {
  plot_index <- plot_index + 1
  # Only the first plot gets the y-axis label
  y_label <- if (plot_index == 1) "Partial effect" else ""
  # Only the last plot gets the caption
  caption_text <- if (plot_index == total_plots) "Basis: TPRS" else NULL

  p_temp <- draw(best$gam, select = "s(temperature_avg)", rug = FALSE, residuals = FALSE) +
    labs(x = "Temperature (deg C)", y = y_label, caption = caption_text) +
    custom_theme +
    coord_cartesian(ylim = c(y_min, y_max))

  for (i in seq_along(p_temp$layers)) {
    if ("colour" %in% names(p_temp$layers[[i]]$aes_params)) p_temp$layers[[i]]$aes_params$colour <- col_temp
    if ("fill" %in% names(p_temp$layers[[i]]$aes_params)) p_temp$layers[[i]]$aes_params$fill <- col_temp_l
  }

  # Add blue flight threshold band (12.7-16 deg C)
  fade_width <- 0.5
  p_temp <- p_temp +
    annotate("rect",
      xmin = 12.7 + fade_width, xmax = 16 - fade_width,
      ymin = -Inf, ymax = Inf, fill = "#ADD8E6", alpha = 0.35
    )
  for (i in 1:5) {
    alpha_val <- 0.35 * (5 - i + 1) / 5
    fade_off <- fade_width * i / 5
    p_temp <- p_temp +
      annotate("rect",
        xmin = 12.7 + fade_width - fade_off,
        xmax = 12.7 + fade_width - fade_off + fade_width / 5,
        ymin = -Inf, ymax = Inf, fill = "#ADD8E6", alpha = alpha_val
      ) +
      annotate("rect",
        xmin = 16 - fade_width + fade_off - fade_width / 5,
        xmax = 16 - fade_width + fade_off,
        ymin = -Inf, ymax = Inf, fill = "#ADD8E6", alpha = alpha_val
      )
  }
  plots[[length(plots) + 1]] <- p_temp
}

if (length(plots) > 0) {
  p13 <- wrap_plots(plots, nrow = 1, ncol = length(plots))
  ggsave(file.path(fig_dir, "partial_effects_30min.png"), p13, width = 14, height = 4.6, dpi = 300, bg = "white")
  ggsave(here("figures", "partial_effects_30min.png"), p13, width = 12, height = 6, dpi = 600, bg = "white")
}

# Export a binned high-res surface for wind x sun interaction
src_file <- here("analysis", "lib", "plot_binned_interaction.R")
if (file.exists(src_file)) source(src_file)
has_wind_sun_tensor <- any(grepl("ti\\(max_gust,butterflies_direct_sun_t_lag\\)",
                                  rownames(sm), fixed = FALSE))
if (exists("create_binned_interaction_plot") && has_wind_sun_tensor) {
  interaction_sizes <- reference_sizes(7, 0.70)
  p_inter_binned <- create_binned_interaction_plot(
    gam_model = best$gam,
    x_var = "max_gust",
    y_var = "butterflies_direct_sun_t_lag",
    data = model_data,
    xlab = "Maximum wind speed (m/s)",
    ylab = "Butterflies in direct sun",
    n = 400,
    limits = c(-6, 6),
    nbreaks = 17,
    breaks = c(-6, -4, -2, 0, 2, 4, 6),
    labels = c("-6", "-4", "-2", "0", "+2", "+4", "+6"),
    too_far = 0.04,
    barheight = 34,
    barwidth = 1.0,
    legend_text_size = interaction_sizes$legend_text,
    legend_title_size = interaction_sizes$legend_title,
    axis_title_size = interaction_sizes$axis_title,
    axis_text_size = interaction_sizes$axis_text,
    base_size = interaction_sizes$axis_title,
    legend_key_height_cm = 1.4
  )
  ggsave(file.path(fig_dir, "interaction_wind_sun_30min.png"), p_inter_binned, width = 7, height = 6, dpi = 300, bg = "white")
  ggsave(here("figures", "interaction_wind_sun_30min.png"), p_inter_binned, width = 7, height = 6, dpi = 600, bg = "white")
} else {
  writeLines(
    paste("Interaction surface not generated because selected model", best_id,
          "does not contain the wind by visible-sun tensor smooth."),
    file.path(text_dir, "interaction_figure_status.txt")
  )
}

# ----------------------------------------------------------------------------
# Request 6: Check if any of the top models include a smooth for wind alone
# ----------------------------------------------------------------------------
wind_smooth_in_top <- tibble(
  Model = top_models$Model,
  Includes_s_max_gust = includes_wind_smooth
)
readr::write_csv(wind_smooth_in_top, file.path(tab_dir, "top5_wind_smooth_presence.csv"))
writeLines(c(
  sprintf("Any top-5 model with s(max_gust)? %s", ifelse(any(includes_wind_smooth), "Yes", "No")),
  paste(wind_smooth_in_top$Model, wind_smooth_in_top$Includes_s_max_gust, sep = ",")
), file.path(text_dir, "wind_smooth_check.txt"))

# ----------------------------------------------------------------------------
# Model diagnostics with autocorrelation plots
# ----------------------------------------------------------------------------
res_df <- tibble(
  fitted = fitted(best$lme),
  resid  = residuals(best$lme, type = "normalized")
)

# Base plots saved via png() to avoid device issues
png(file.path(fig_dir, "acf_30min.png"), width = 900, height = 600)
acf_cex <- acf_cex_like_reference(7, 0.70)
par(cex.lab = acf_cex$lab, cex.axis = acf_cex$axis, cex.main = acf_cex$lab, mar = c(5, 5, 2, 2))
acf(res_df$resid, main = "ACF of normalized residuals")
dev.off()
png(here("figures", "acf_30min.png"), width = 7, height = 5, units = "in", res = 600)
par(cex.lab = acf_cex$lab, cex.axis = acf_cex$axis, cex.main = acf_cex$lab, mar = c(5, 5, 2, 2))
acf(res_df$resid, main = "", xlab = "Lag", ylab = "Autocorrelation")
dev.off()

png(file.path(fig_dir, "diag_pacf.png"), width = 900, height = 600)
pacf(res_df$resid, main = "PACF of normalized residuals")
dev.off()

diagnostic_theme <- theme_like_reference(9, 0.80)

# Combined 1x2 diagnostic panel: Q-Q plot and Residuals vs Fitted
diag_scatter <- ggplot(res_df, aes(fitted, resid)) +
  geom_point(alpha = 0.25, size = 0.8, color = "#4d4d4d") +
  geom_smooth(se = FALSE, color = "#2c7fb8", linewidth = 0.8, method = "loess", span = 0.8) +
  geom_hline(yintercept = 0, color = "gray65") +
  labs(x = "Fitted values", y = "Standardized residuals") +
  diagnostic_theme

diag_qq <- ggplot(res_df, aes(sample = resid)) +
  stat_qq(alpha = 0.25, size = 0.8, color = "#4d4d4d") +
  stat_qq_line(color = "#2c7fb8", linewidth = 0.8) +
  labs(x = "Theoretical quantiles", y = "Sample quantiles") +
  diagnostic_theme

diag_1x2 <- wrap_plots(diag_qq, diag_scatter, nrow = 1, ncol = 2)
ggsave(file.path(fig_dir, "diagnostics_30min.png"), diag_1x2, width = 12, height = 5, dpi = 300, bg = "white")
ggsave(here("figures", "diagnostics_30min.png"), diag_1x2, width = 9, height = 5, dpi = 600, bg = "white")

# ----------------------------------------------------------------------------
# Minimal console summary & pointers
# ----------------------------------------------------------------------------
message(sprintf("\nExport complete. Outputs in: %s\n- Text: %s\n- Tables: %s\n- Figures: %s\n", export_dir, text_dir, tab_dir, fig_dir))
