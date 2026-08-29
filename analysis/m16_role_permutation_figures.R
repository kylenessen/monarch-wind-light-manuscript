#!/usr/bin/env Rscript

# Compare all six assignments of wind, temperature, and direct-sun count to
# the x-axis, line color, and figure panels for the selected M16 model.

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(here)
  library(grid)
  library(mgcv)
  library(nlme)
  library(patchwork)
  library(readr)
  library(tibble)
})

source(here("analysis", "lib", "manuscript_figure_style.R"))

out_dir <- here(
  "analysis", "outputs", "30_minute", "m16", "figures", "candidates",
  "role_permutations"
)
table_dir <- here(
  "analysis", "outputs", "30_minute", "m16", "tables"
)
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(table_dir, recursive = TRUE, showWarnings = FALSE)

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

model <- gamm(
  butterfly_difference_cbrt ~
    total_butterflies_t_lag +
    max_gust * temperature_avg * butterflies_direct_sun_t_lag,
  data = data,
  random = list(
    deployment_id = ~1,
    deployment_day = ~1
  ),
  correlation = corAR1(
    form = ~ observation_order_within_day_t | deployment_day
  ),
  method = "REML"
)

previous_bi_value <- median(data$total_butterflies_t_lag)
wind_cap <- unname(quantile(data$max_gust, 0.99))

variable_specs <- list(
  wind = list(
    column = "max_gust",
    short_name = "Wind",
    legend_name = "Maximum wind gust",
    axis_label = "Maximum wind gust (m/s)",
    levels = unname(quantile(data$max_gust, c(0.25, 0.50, 0.75))),
    x_range = c(0, wind_cap),
    x_breaks = c(0, 2, 4, 6),
    distance_scale = sd(data$max_gust),
    colors = c("#56B4E9", "#009E73", "#D55E00")
  ),
  temperature = list(
    column = "temperature_avg",
    short_name = "Temperature",
    legend_name = "Temperature",
    axis_label = "Temperature (°C)",
    levels = c(10, 15, 20),
    x_range = c(10, 20),
    x_breaks = c(10, 15, 20),
    distance_scale = sd(data$temperature_avg),
    colors = c("#0072B2", "#E69F00", "#D55E00")
  ),
  direct_sun = list(
    column = "butterflies_direct_sun_t_lag",
    short_name = "Direct sun",
    legend_name = "Butterflies visible in direct sun",
    axis_label = "Butterflies visible in direct sun",
    levels = c(0, 3, 20),
    x_range = c(0, 20),
    x_breaks = c(0, 10, 20),
    distance_scale = IQR(
      data$butterflies_direct_sun_t_lag[
        data$butterflies_direct_sun_t_lag > 0
      ]
    ),
    colors = c("#4D4D4D", "#2B83BA", "#D7191C")
  )
)

format_level <- function(variable, value) {
  if (variable == "temperature") {
    return(paste0(format(value, trim = TRUE), " °C"))
  }
  if (variable == "wind") {
    return(paste0(format(round(value, 1), nsmall = 1, trim = TRUE), " m/s"))
  }
  format(round(value, 0), trim = TRUE)
}

make_role_plot <- function(x_variable, line_variable, facet_variable, tag) {
  x_spec <- variable_specs[[x_variable]]
  line_spec <- variable_specs[[line_variable]]
  facet_spec <- variable_specs[[facet_variable]]

  grid <- expand.grid(
    x_value = seq(x_spec$x_range[1], x_spec$x_range[2], length.out = 180),
    line_value = line_spec$levels,
    facet_value = facet_spec$levels,
    KEEP.OUT.ATTRS = FALSE
  ) %>%
    as_tibble() %>%
    mutate(total_butterflies_t_lag = previous_bi_value)

  grid[[x_spec$column]] <- grid$x_value
  grid[[line_spec$column]] <- grid$line_value
  grid[[facet_spec$column]] <- grid$facet_value

  prediction <- predict(model$gam, newdata = grid, se.fit = TRUE)
  grid <- grid %>%
    mutate(
      fit = as.numeric(prediction$fit),
      standard_error = as.numeric(prediction$se.fit),
      conf_low = fit - 1.96 * standard_error,
      conf_high = fit + 1.96 * standard_error,
      supported = FALSE
    )

  support_rows <- list()
  for (line_value in line_spec$levels) {
    for (facet_value in facet_spec$levels) {
      distance <- sqrt(
        ((data[[line_spec$column]] - line_value) /
          line_spec$distance_scale)^2 +
        ((data[[facet_spec$column]] - facet_value) /
          facet_spec$distance_scale)^2
      )
      nearby_rows <- order(distance)[seq_len(50)]
      local_x <- data[[x_spec$column]][nearby_rows]
      local_lower <- max(min(local_x), x_spec$x_range[1])
      local_upper <- min(max(local_x), x_spec$x_range[2])
      grid_rows <- grid$line_value == line_value &
        grid$facet_value == facet_value
      grid$supported[grid_rows] <-
        grid$x_value[grid_rows] >= local_lower &
        grid$x_value[grid_rows] <= local_upper
      support_rows[[length(support_rows) + 1]] <- tibble(
        plot = tag,
        x_variable = x_variable,
        line_variable = line_variable,
        facet_variable = facet_variable,
        line_value = line_value,
        facet_value = facet_value,
        nearby_observations = length(nearby_rows),
        displayed_x_lower = local_lower,
        displayed_x_upper = local_upper
      )
    }
  }

  line_labels <- vapply(
    line_spec$levels,
    function(value) format_level(line_variable, value),
    character(1)
  )
  facet_labels <- vapply(
    facet_spec$levels,
    function(value) format_level(facet_variable, value),
    character(1)
  )
  color_values <- setNames(line_spec$colors, line_labels)

  grid <- grid %>%
    mutate(
      fit_supported = if_else(supported, fit, NA_real_),
      conf_low_supported = if_else(supported, conf_low, NA_real_),
      conf_high_supported = if_else(supported, conf_high, NA_real_),
      line_label = factor(
        line_value,
        levels = line_spec$levels,
        labels = line_labels
      ),
      facet_label = factor(
        facet_value,
        levels = facet_spec$levels,
        labels = facet_labels
      ),
      plot = tag,
      x_variable = x_variable,
      line_variable = line_variable,
      facet_variable = facet_variable
    )

  plot_title <- paste0(
    tag, ". x = ", x_spec$short_name,
    "  |  lines = ", line_spec$short_name,
    "  |  panels = ", facet_spec$short_name
  )

  plot <- ggplot(
    grid,
    aes(
      x = x_value,
      y = fit_supported,
      color = line_label,
      fill = line_label,
      group = line_label
    )
  ) +
    geom_ribbon(
      aes(ymin = conf_low_supported, ymax = conf_high_supported),
      alpha = 0.08,
      linewidth = 0,
      color = NA,
      na.rm = TRUE
    ) +
    geom_line(linewidth = 0.95, na.rm = TRUE) +
    geom_hline(yintercept = 0, color = "gray55", linewidth = 0.5) +
    facet_wrap(~facet_label, nrow = 1) +
    scale_color_manual(values = color_values, name = line_spec$legend_name) +
    scale_fill_manual(values = color_values, name = line_spec$legend_name) +
    scale_x_continuous(
      breaks = x_spec$x_breaks,
      expand = expansion(mult = c(0, 0.02))
    ) +
    labs(
      title = plot_title,
      x = x_spec$axis_label,
      y = "Modeled 30-minute BI change\n(cube-root scale)"
    ) +
    theme_like_reference(12, 0.95) +
    theme(
      legend.position = "bottom",
      plot.title = element_text(size = 13, face = "bold", hjust = 0),
      strip.text = element_text(color = "black"),
      panel.spacing.x = unit(3, "lines")
    )

  list(
    plot = plot,
    predictions = grid,
    support = bind_rows(support_rows)
  )
}

permutations <- tribble(
  ~tag, ~x_variable, ~line_variable, ~facet_variable, ~file_name,
  "A", "wind", "direct_sun", "temperature", "a_x_wind_lines_sun_panels_temperature.png",
  "B", "wind", "temperature", "direct_sun", "b_x_wind_lines_temperature_panels_sun.png",
  "C", "temperature", "wind", "direct_sun", "c_x_temperature_lines_wind_panels_sun.png",
  "D", "temperature", "direct_sun", "wind", "d_x_temperature_lines_sun_panels_wind.png",
  "E", "direct_sun", "wind", "temperature", "e_x_sun_lines_wind_panels_temperature.png",
  "F", "direct_sun", "temperature", "wind", "f_x_sun_lines_temperature_panels_wind.png"
)

results <- lapply(seq_len(nrow(permutations)), function(i) {
  result <- make_role_plot(
    permutations$x_variable[i],
    permutations$line_variable[i],
    permutations$facet_variable[i],
    permutations$tag[i]
  )
  ggsave(
    file.path(out_dir, permutations$file_name[i]),
    result$plot,
    width = 12,
    height = 5.8,
    dpi = 300,
    bg = "white"
  )
  result
})

overview_breaks <- list(
  wind = c(0, 3, 6),
  temperature = c(10, 20),
  direct_sun = c(0, 20)
)
overview_plots <- lapply(seq_along(results), function(i) {
  x_variable <- permutations$x_variable[i]
  results[[i]]$plot +
    scale_x_continuous(
      breaks = overview_breaks[[x_variable]],
      expand = expansion(mult = c(0, 0.02))
    )
})

overview <- wrap_plots(
  overview_plots,
  ncol = 2
) +
  plot_annotation(
    title = "M16 three-way interaction role permutations",
    subtitle = paste(
      "Predictions hold previous BI at 37. Lines use local observed ranges.",
      "Wind is capped at its overall 99th percentile."
    ),
    theme = theme(
      plot.title = element_text(size = 20, face = "bold"),
      plot.subtitle = element_text(size = 13)
    )
  )

ggsave(
  file.path(out_dir, "m16_role_permutations_overview.png"),
  overview,
  width = 18,
  height = 19,
  dpi = 240,
  bg = "white"
)

write_csv(
  bind_rows(lapply(results, `[[`, "predictions")),
  file.path(table_dir, "m16_role_permutation_predictions.csv")
)
write_csv(
  bind_rows(lapply(results, `[[`, "support")),
  file.path(table_dir, "m16_role_permutation_support_ranges.csv")
)

message("Wrote M16 role-permutation figures to ", out_dir)
