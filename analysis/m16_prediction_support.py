# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "numpy>=2.3.0",
#   "pandas>=2.3.0",
#   "scipy>=1.16.0",
# ]
# ///

"""Estimate deployment-balanced central predictor support for M16 slices."""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "monarch_analysis_lag30min.csv"
OUTPUT_PATH = (
    ROOT
    / "analysis"
    / "outputs"
    / "30_minute"
    / "m16"
    / "tables"
    / "m16_prediction_support_intervals.csv"
)

TEMPERATURE_VALUES = (10.0, 15.0, 20.0)
SUN_VALUES = (0.0, 7.0, 20.0)
COVERAGE_VALUES = (0.95, 0.975, 0.99)
RANDOM_SEED = 20260828
RANDOM_DIRECTIONS = 8192

REQUIRED_COLUMNS = [
    "butterfly_difference_cbrt",
    "total_butterflies_t_lag",
    "temperature_avg",
    "max_gust",
    "butterflies_direct_sun_t_lag",
    "observation_order_within_day_t",
    "deployment_day",
    "deployment_id",
]
PREDICTOR_COLUMNS = [
    "max_gust",
    "temperature_avg",
    "butterflies_direct_sun_t_lag",
]


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    ordered_values = values[order]
    cumulative_weight = np.cumsum(weights[order])
    index = np.searchsorted(cumulative_weight, q * cumulative_weight[-1], side="left")
    return float(ordered_values[index])


def weighted_directional_depth(
    points: np.ndarray, directions: np.ndarray, weights: np.ndarray
) -> np.ndarray:
    normalized_weights = weights / weights.sum()
    depth = np.ones(len(points))
    for direction in directions:
        projection = points @ direction
        order = np.argsort(projection)
        cumulative_below = np.cumsum(normalized_weights[order])
        cumulative_above = np.cumsum(normalized_weights[order][::-1])[::-1]
        directional_depth = np.empty(len(points))
        directional_depth[order] = np.minimum(cumulative_below, cumulative_above)
        depth = np.minimum(depth, directional_depth)
    return depth


def intersect_gust_slice(
    hull: ConvexHull, temperature: float, sun_exposed_bi: float
) -> tuple[float, float] | None:
    lower = -np.inf
    upper = np.inf
    fixed = np.array([temperature, sun_exposed_bi])

    for equation in hull.equations:
        gust_coefficient = equation[0]
        fixed_value = float(np.dot(equation[1:-1], fixed) + equation[-1])
        if abs(gust_coefficient) < 1e-12:
            if fixed_value > 1e-9:
                return None
        elif gust_coefficient > 0:
            upper = min(upper, -fixed_value / gust_coefficient)
        else:
            lower = max(lower, -fixed_value / gust_coefficient)

    if lower > upper:
        return None
    return max(0.0, lower), upper


def main() -> None:
    data = pd.read_csv(DATA_PATH).dropna(subset=REQUIRED_COLUMNS).reset_index(drop=True)
    if len(data) != 1894:
        raise ValueError(f"Expected 1,894 complete M16 rows, found {len(data):,}.")

    predictors = data[PREDICTOR_COLUMNS].to_numpy(float)
    center = predictors.mean(axis=0)
    covariance = np.cov(predictors, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    whitener = eigenvectors @ np.diag(1.0 / np.sqrt(eigenvalues)) @ eigenvectors.T
    whitened = (predictors - center) @ whitener

    rng = np.random.default_rng(RANDOM_SEED)
    random_directions = rng.normal(size=(RANDOM_DIRECTIONS, predictors.shape[1]))
    random_directions /= np.linalg.norm(random_directions, axis=1, keepdims=True)
    observation_directions = whitened / np.maximum(
        np.linalg.norm(whitened, axis=1, keepdims=True), 1e-12
    )
    directions = np.vstack(
        [
            random_directions,
            observation_directions,
            -observation_directions,
            np.eye(predictors.shape[1]),
            -np.eye(predictors.shape[1]),
        ]
    )

    deployment_sizes = data.groupby("deployment_id")["deployment_id"].transform("size")
    weights = 1.0 / deployment_sizes.to_numpy(float)
    weights /= weights.sum()
    depth = weighted_directional_depth(whitened, directions, weights)

    rows = []
    for coverage in COVERAGE_VALUES:
        depth_cutoff = weighted_quantile(depth, weights, 1.0 - coverage)
        retained = depth >= depth_cutoff
        hull = ConvexHull(predictors[retained], qhull_options="QJ")
        retained_weight = float(weights[retained].sum())

        for temperature in TEMPERATURE_VALUES:
            for sun_exposed_bi in SUN_VALUES:
                interval = intersect_gust_slice(hull, temperature, sun_exposed_bi)
                if interval is None:
                    support_min = np.nan
                    support_max = np.nan
                else:
                    support_min, support_max = interval
                rows.append(
                    {
                        "central_coverage": coverage,
                        "temperature_c": temperature,
                        "sun_exposed_bi": sun_exposed_bi,
                        "gust_support_min_ms": support_min,
                        "gust_support_max_ms": support_max,
                        "depth_cutoff": depth_cutoff,
                        "retained_rows": int(retained.sum()),
                        "retained_deployment_weight": retained_weight,
                        "random_seed": RANDOM_SEED,
                        "random_directions": RANDOM_DIRECTIONS,
                    }
                )

    output = pd.DataFrame(rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False, float_format="%.8f")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
