from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app.services.forecasting.base import ForecastModel


class ExponentialSmoothingModel(ForecastModel):
    """
    Holt-Winters exponential smoothing via statsmodels.

    - Uses additive trend when enough data exists to estimate one.
    - Uses additive weekly seasonality (period=7) when there are at
      least 2 full seasonal cycles (14+ days) of data, since retail
      demand very commonly has weekday/weekend structure.
    - Falls back to simple (level-only) exponential smoothing when data
      is too short for trend/seasonality to be estimated reliably.
    """

    name = "ExponentialSmoothing"
    min_observations = 10

    def __init__(self):
        self._fitted = None
        self._resid_std = 0.0

    def fit(self, series: pd.Series) -> "ExponentialSmoothingModel":
        values = series.values.astype(float)
        n = len(values)

        use_seasonal = n >= 14
        use_trend = n >= 10

        seasonal = "add" if use_seasonal else None
        seasonal_periods = 7 if use_seasonal else None
        trend = "add" if use_trend else None

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                model = ExponentialSmoothing(
                    values,
                    trend=trend,
                    seasonal=seasonal,
                    seasonal_periods=seasonal_periods,
                    initialization_method="estimated",
                )
                self._fitted = model.fit(optimized=True)
            except Exception:
                # Fall back to the simplest possible smoothing if the
                # richer model fails to converge (common with short or
                # degenerate series).
                model = ExponentialSmoothing(
                    values, trend=None, seasonal=None, initialization_method="estimated"
                )
                self._fitted = model.fit(optimized=True)

        residuals = self._fitted.resid
        self._resid_std = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0
        return self

    def predict(self, horizon: int) -> np.ndarray:
        forecast = self._fitted.forecast(horizon)
        return np.clip(np.asarray(forecast, dtype=float), 0, None)

    def prediction_std(self) -> float:
        return self._resid_std
