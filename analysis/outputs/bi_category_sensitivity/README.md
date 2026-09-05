# Butterfly Index category-value sensitivity

This analysis evaluates whether the retained results depend on assigning the
minimum value to each ordinal image-classification category. It regenerates the
30-minute and Next Day Window datasets using four mappings for the categories
1--9, 10--99, and 100--999.

The mappings are the original lower bounds (1, 10, 100), rounded geometric
midpoints (3, 32, 316), rounded arithmetic midpoints (5, 55, 550), and upper
bounds (9, 99, 999). Values of zero and 1000 or more remain zero and 1000.

Run the analysis from the repository root with:

```sh
uv run analysis/prepare_bi_category_sensitivity.py
Rscript analysis/bi_category_sensitivity_analysis.R
```

The data subdirectory contains regenerated intermediate datasets. The summary
CSVs report focused sensitivity checks for M16 and M32. This analysis does not
estimate inter-observer agreement because the original observers classified
non-overlapping image sets.

Across all four mappings, the 30-minute three-way interaction remained strongly
supported, with p-values between 1.21e-9 and 1.27e-9. Removing the three-way
term increased AIC by 34.74 to 34.85, and the conditional wind patterns at cool,
intermediate, and warm temperatures retained the same directions. Adjusted
R-squared values ranged from 0.0511 to 0.0517.

The selected Next Day M32 interaction also remained supported across mappings,
with p-values from 0.00083 to 0.00137 and adjusted R-squared values from 0.391
to 0.397. In a focused comparison with the null linear baseline, M32 was favored
by 2.45 to 3.58 AICc units.

Adding observer as a fixed effect did not improve the lower-bound M16 fit. The
likelihood-ratio test gave p = 0.957, and the three-way estimate and uncertainty
were effectively unchanged. This is a robustness check for mean observer
differences. It is not an inter-observer agreement analysis.
