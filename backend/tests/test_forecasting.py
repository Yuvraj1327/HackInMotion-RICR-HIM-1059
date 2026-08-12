from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from app.services.forecast_service import InsufficientDataError, generate_product_forecast
from app.services.forecasting.model_selector import select_and_forecast


def _make_df(quantities, promotions=None):
    days = len(quantities)
    dates = [date.today() - timedelta(days=days - 1 - i) for i in range(days)]
    return pd.DataFrame(
        {
            "date": pd.to_datetime(dates),
            "quantity": quantities,
            "promotion": promotions or [0] * days,
        }
    )


def test_forecast_with_strong_weekly_pattern_uses_smoothing_or_ma():
    rng = np.random.default_rng(0)
    dates = [date.today() - timedelta(days=119 - i) for i in range(120)]
    q = [max(0, rng.normal(30 * (1.4 if d.weekday() >= 5 else 1.0), 3)) for d in dates]
    df = _make_df(q)
    result = select_and_forecast(df, horizon=7)
    assert result.model_name in ("ExponentialSmoothing", "MovingAverage", "XGBoost")
    assert len(result.forecast) == 7
    assert all(f >= 0 for f in result.forecast)


def test_insufficient_data_uses_fallback_without_crashing():
    df = _make_df([5, 7])  # only 2 days
    result = select_and_forecast(df, horizon=7)
    assert result.model_name == "HistoricalAverageFallback"
    assert len(result.forecast) == 7


def test_zero_sales_history_does_not_crash():
    df = _make_df([0] * 30)
    result = select_and_forecast(df, horizon=7)
    assert all(f == 0 for f in result.forecast)


def test_constant_demand_does_not_crash():
    df = _make_df([10] * 40)
    result = select_and_forecast(df, horizon=7)
    assert len(result.forecast) == 7


def test_extreme_outliers_do_not_crash():
    rng = np.random.default_rng(1)
    q = list(np.clip(rng.normal(20, 3, 60), 0, None).round())
    q[30] = 5000  # extreme outlier
    df = _make_df(q)
    result = select_and_forecast(df, horizon=7)
    assert len(result.forecast) == 7
    assert all(np.isfinite(f) for f in result.forecast)


def test_generate_product_forecast_raises_on_empty_sales():
    with pytest.raises(InsufficientDataError):
        generate_product_forecast([], horizon_days=7)


def test_generate_product_forecast_returns_valid_structure():
    rows = [
        {"sale_date": (date.today() - timedelta(days=30 - i)).isoformat(), "quantity": 10 + i % 5, "promotion": False}
        for i in range(30)
    ]
    result = generate_product_forecast(rows, horizon_days=7)
    assert len(result.points) == 7
    for p in result.points:
        assert p["predicted_demand"] >= 0
        assert p["lower_bound"] <= p["predicted_demand"] <= p["upper_bound"]
    assert 0 <= result.confidence <= 1


@pytest.mark.parametrize("horizon", [7, 14, 30])
def test_supports_all_allowed_horizons(horizon):
    rows = [
        {"sale_date": (date.today() - timedelta(days=60 - i)).isoformat(), "quantity": 15, "promotion": False}
        for i in range(60)
    ]
    result = generate_product_forecast(rows, horizon_days=horizon)
    assert len(result.points) == horizon
