# Does Wind Disrupt Overwintering Monarch Butterfly Clusters?

An observational study of western monarchs by Kyle Nessen, Peter C. Ibsen, Jay E. Diffendorfer, and Francis X. Villablanca.

[Read the manuscript](output/pdf/manuscript.pdf). This is the manuscript submitted to *Insects* on September 24, 2026, including its appendices. The [dated submission release](https://github.com/kylenessen/monarch-wind-light-manuscript/releases/tag/submission-2026-09-24) preserves the submission package and an identifiable repository version. Submission does not imply acceptance or publication. The study extends [Kyle Nessen's master's thesis](https://digitalcommons.calpoly.edu/theses/3180/).

To explore the evidence, start with the [data guide](data/README.md) and [analysis guide](analysis/README.md). The [complete model comparisons](analysis/outputs/harmonized_model_comparison/README.md) and [Butterfly Index sensitivity checks](analysis/outputs/bi_category_sensitivity/README.md) include saved results. Reading them does not require running code.

The [USGS data release](https://doi.org/10.5066/P13IEKEB) documents the photographs, deployment metadata, image-level classification summaries, wind records and reviewed temperatures. Its assigned publication date is September 30, 2026. The DOI may not resolve before release activation. The repository already includes the manuscript's analysis inputs and outputs. [Release tables](data/release/README.md) document the broader observation archive and known gaps.

The [classifier repository](https://github.com/kylenessen/monarch_trailcam_classifier) contains the image-classification application and original cell-level annotations. The [illustrated protocol](https://kylenessen.github.io/monarch_trailcam_classifier/) is preserved as the guide shared with the labeling team. Current installation instructions are provided separately in the classifier repository.

The manuscript source is [manuscript.tex](manuscript.tex). Its four figures are the [monitoring photograph](figures/methods_photo.jpg), [descriptive figure](figures/descriptive_bi.png), [30-minute predictions](analysis/outputs/harmonized_model_comparison/figures/thirty_minute_predicted_response.png), and [Next Day interaction](analysis/outputs/next_day_window/figures/interaction_wind_sun_nextday.png). The bibliography and journal template are in [bibliography](bibliography/) and [Definitions](Definitions/). The compressed photograph is used in the manuscript. Its [high-resolution original](figures/methods_photo.png) is retained.

To compile the paper, install a TeX distribution with `latexmk` and run the following commands from the repository root. The saved figures are sufficient.

```sh
mkdir -p output/pdf
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=output/pdf manuscript.tex
```

To rerun the analyses, follow the [analysis guide](analysis/README.md). Python dependencies are recorded in `uv.lock`. R dependencies are recorded in `renv.lock`. The guide separates reproduction using the included inputs from preparation of the larger observational release, which requires the photograph archive.

Citation metadata is in [CITATION.cff](CITATION.cff). Original analysis and utility code is dedicated to the public domain under [CC0 1.0](LICENSE). [Reuse notes](REUSE.md) explain the separate status of manuscript text, data and third-party assets. Questions and reproducibility problems can be reported through [GitHub issues](https://github.com/kylenessen/monarch-wind-light-manuscript/issues). See [CONTRIBUTING.md](CONTRIBUTING.md) before changing analytical inputs or outputs.

Earlier submissions remain available on [first-submission](https://github.com/kylenessen/monarch-wind-light-manuscript/tree/first-submission) and [second-submission](https://github.com/kylenessen/monarch-wind-light-manuscript/tree/second-submission). The second branch preserves the September 4 revision, reviewer responses, cover letter and superseded analyses. The September 24 release is the final submitted version. [Review records](research/README.md) describe verification and provenance. Historical drive operations and equipment notes are kept separately from scientific review records.
