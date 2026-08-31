# Monarch Wind and Light Manuscript

This repository contains the manuscript, analysis data, and reproducibility materials for "Wind Associations with Overwintering Monarch Butterfly Cluster Size Depend on Temperature and Sun Exposure" by Kyle Nessen, Peter C. Ibsen, Jay Diffendorfer, and Francis X. Villablanca.

The manuscript extends the work in [Kyle Nessen's master's thesis](https://digitalcommons.calpoly.edu/theses/3180/) and provides the publication version of the wind analysis. The repository is intended to make the written paper, analysis inputs, statistical scripts, generated summaries, and figures traceable from source data through manuscript output.

## Repository Contents

`manuscript.tex` is the main LaTeX manuscript file. `manuscript.pdf` is the compiled manuscript output when present in a local checkout.

The `data/` directory contains the deployment metadata, hand-labeled classification files, wind sensor databases, temperature data, and generated analysis CSV files used by the statistical analyses. See `data/README.md` for details about included data and data availability limits.

The `analysis/` directory contains the Python data preparation scripts, R analysis scripts, model outputs, generated summaries, and analysis provenance notes. See `analysis/README.md` for the commands used to regenerate the analysis datasets and figures.

The `figures/` directory contains manuscript figures and supporting source files. The `bibliography/` and `Definitions/` directories contain the BibTeX references and journal template files used to build the manuscript.

## Reproducibility

Run Python scripts with `uv` from the repository root. Run R scripts with `Rscript` from the repository root. The focused commands for rebuilding analysis datasets and manuscript figures are documented in `analysis/README.md`.

Raw image files and the classification review software are not included in this repository because of storage constraints. See `data/README.md` for the current data availability notes.
