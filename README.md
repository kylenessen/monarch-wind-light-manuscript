# Does Wind Disrupt Overwintering Monarch Butterfly Clusters?

An observational study of western monarchs by Kyle Nessen, Peter C. Ibsen, Jay E. Diffendorfer, and Francis X. Villablanca.

[Read the manuscript](output/pdf/manuscript.pdf). This is the revised submission, including its appendices. The study extends [Kyle Nessen's master's thesis](https://digitalcommons.calpoly.edu/theses/3180/).

To explore the evidence, start with the [data guide](data/README.md) and the [analysis guide](analysis/README.md). The [complete model comparisons](analysis/outputs/harmonized_model_comparison/README.md) and [Butterfly Index sensitivity checks](analysis/outputs/bi_category_sensitivity/README.md) include the saved results, so reading them does not require running code.

The manuscript source is [manuscript.tex](manuscript.tex). Its four figures are the [monitoring photograph](figures/methods_photo.png), [descriptive figure](figures/descriptive_bi.png), [30-minute predictions](analysis/outputs/harmonized_model_comparison/figures/thirty_minute_predicted_response.png), and [Next Day interaction](analysis/outputs/next_day_window/figures/interaction_wind_sun_nextday.png). [bibliography/](bibliography/) contains the references. [Definitions/](Definitions/) contains the journal's LaTeX template and supporting assets.

To compile the paper, install a TeX distribution with `latexmk` and run these commands from the repository root. The saved figures are sufficient. No analysis rerun is required.

```sh
mkdir -p output/pdf
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=output/pdf manuscript.tex
```

The [analysis guide](analysis/README.md) documents Python and R setup and the commands for regenerating inputs, results, and figures. The source classifications, wind databases, and reviewed temperature records are included. Original photographs are excluded for storage reasons. The USGS ScienceBase release is planned for publication on September 30, 2026, with its final citation and DOI pending. See the [data availability notes](data/README.md) and [draft release tables](data/release/README.md) for scope and known gaps.

Both submission states are preserved as Git branches. [first-submission](https://github.com/kylenessen/monarch-wind-light-manuscript/tree/first-submission) records the original submission at `12b7cc9`. [second-submission](https://github.com/kylenessen/monarch-wind-light-manuscript/tree/second-submission) records the revised submission at `a2a57f8`, before repository cleanup. The second branch also preserves the reviewer responses, cover letter, submitted Word files, revision notes, and superseded analyses. To revisit a submission locally, commit or stash any current changes, then use `git switch first-submission` or `git switch second-submission`. Return with `git switch main`.
