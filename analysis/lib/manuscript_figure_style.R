reference_figure_style <- list(
  figure_width = 7,
  include_width = 0.95,
  axis_title = 14,
  axis_text = 12,
  legend_title = 14,
  legend_text = 12
)

reference_scale <- function(fig_width, include_width, reference = reference_figure_style) {
  (fig_width / reference$figure_width) * (reference$include_width / include_width)
}

reference_text_size <- function(size, fig_width, include_width, reference = reference_figure_style) {
  round(size * reference_scale(fig_width, include_width, reference))
}

reference_sizes <- function(fig_width, include_width, reference = reference_figure_style) {
  list(
    axis_title = reference_text_size(reference$axis_title, fig_width, include_width, reference),
    axis_text = reference_text_size(reference$axis_text, fig_width, include_width, reference),
    legend_title = reference_text_size(reference$legend_title, fig_width, include_width, reference),
    legend_text = reference_text_size(reference$legend_text, fig_width, include_width, reference)
  )
}

theme_like_reference <- function(fig_width,
                                 include_width,
                                 reference = reference_figure_style,
                                 grid_minor = TRUE,
                                 bold_axis_title = FALSE) {
  sizes <- reference_sizes(fig_width, include_width, reference)
  axis_face <- if (bold_axis_title) "bold" else "plain"

  theme_minimal(base_size = sizes$axis_title) +
    theme(
      panel.grid.major = element_line(color = "gray90", linewidth = 0.5),
      panel.grid.minor = if (grid_minor) element_line(color = "gray95", linewidth = 0.3) else element_blank(),
      axis.text = element_text(color = "black", size = sizes$axis_text),
      axis.title = element_text(color = "black", size = sizes$axis_title, face = axis_face),
      plot.title = element_blank(),
      plot.subtitle = element_blank(),
      plot.caption = element_blank(),
      legend.title = element_text(size = sizes$legend_title),
      legend.text = element_text(size = sizes$legend_text)
    )
}

acf_cex_like_reference <- function(fig_width, include_width, reference = reference_figure_style) {
  sizes <- reference_sizes(fig_width, include_width, reference)
  list(
    lab = sizes$axis_title / 12,
    axis = sizes$axis_text / 12
  )
}

ggplot_text_size <- function(pt_size) {
  pt_size / getFromNamespace(".pt", "ggplot2")
}
