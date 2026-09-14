"""Public analysis names and lossless selection from historical manuscript inputs."""

import numpy as np
import pandas as pd


THIRTY_COLUMNS = {
    "deployment_id": "deployment_id",
    "deployment_day": "deployment_day_id",
    "observation_order_within_day_t": "observation_order",
    "image_filename_t_lag": "previous_image_filename",
    "timestamp_t_lag": "previous_timestamp_recorded",
    "image_filename_t": "current_image_filename",
    "timestamp_t": "current_timestamp_recorded",
    "total_butterflies_t_lag": "previous_bi",
    "total_butterflies_t": "current_bi",
    "butterfly_difference": "delta_bi",
    "butterfly_difference_cbrt": "delta_bi_signed_cuberoot",
    "butterflies_direct_sun_t_lag": "previous_sun_exposed_bi",
    "temperature_avg": "mean_temperature_c",
    "max_gust": "maximum_wind_gust_m_s",
    "time_within_day_t": "minutes_since_first_daily_observation",
    "minutes_above_threshold": "minutes_gust_at_or_above_2_m_s",
    "Observer": "primary_observer",
}

NEXT_COLUMNS = {
    "deployment_id": "deployment_id",
    "observation_order_t": "observation_order",
    "max_butterflies_t_1": "previous_day_maximum_bi",
    "butterfly_diff": "delta_bi",
    "lag_duration_hours": "window_duration_hours",
    "temp_min": "minimum_temperature_c",
    "temp_max": "maximum_temperature_c",
    "temp_at_max_count_t_1": "temperature_at_previous_day_maximum_c",
    "wind_max_gust": "maximum_wind_gust_m_s",
    "sum_butterflies_direct_sun": "cumulative_sun_exposed_bi",
}


def analysis_30_minute(source):
    expected = source.total_butterflies_t - source.total_butterflies_t_lag
    np.testing.assert_allclose(source.butterfly_difference, expected)
    np.testing.assert_allclose(source.butterfly_difference_cbrt, np.cbrt(expected))
    # Keep row order and the stored transformation to avoid changing fitted inputs.
    result = source[list(THIRTY_COLUMNS)].rename(columns=THIRTY_COLUMNS).copy()
    assert not result.isna().any().any()
    return result


def analysis_next_day(source):
    required = list(NEXT_COLUMNS)
    selected = source.loc[source.metrics_complete.ge(0.95) & source[required].notna().all(axis=1)]
    np.testing.assert_allclose(selected.butterfly_diff,
                               selected.max_butterflies_t - selected.max_butterflies_t_1)
    return selected[list(NEXT_COLUMNS)].rename(columns=NEXT_COLUMNS).sort_values(
        ["deployment_id", "observation_order"]).reset_index(drop=True)


def has_classification(record, *, author_accepted=False):
    """Retain confirmed zeros and saved annotations, omit untouched zero placeholders."""
    return bool(author_accepted or record.get("confirmed") or record.get("user") or any(
        str(cell.get("count", "0")) != "0" or cell.get("directSun", cell.get("sunlight", False))
        for cell in record.get("cells", {}).values()))
