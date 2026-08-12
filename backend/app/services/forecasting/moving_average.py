from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.forecasting.base import ForecastModel


class MovingAverageModel(ForecastModel):
    """
    Simple baseline: forecast = average of the last `window` days of
    demand, held flat across the whole horizon. Used both as a
    standalone candidate model and as the ultimate fallback when a
    product has too little history for anything smarter.
    """

    name = "MovingAverage"
    min_observations = 3

    def __init__(self, window: int = 7):
        self.window = window
        self._level: float = 0.0
        self._std: float = 0.0

    def fit(self, series: pd.Series) -> "MovingAverageModel":
        w = min(self.window, len(series))
        w = max(w, 1)
        recent = series.iloc[-w:]
        self._level = float(recent.mean())
        self._std = float(recent.std(ddof=1)) if len(recent) > 1 else 0.0
        return self

    def predict(self, horizon: int) -> np.ndarray:
        return np.full(horizon, max(self._level, 0.0))

    def prediction_std(self) -> float:
        return self._std


class HistoricalAverageFallback(ForecastModel):
    """
    Absolute last-resort fallback for products with almost no data
    (even fewer points than MovingAverage needs): forecast = the
    all-time average of whatever sales exist, or 0 if there are none.
    """

    name = "HistoricalAverageFallback"
    min_observations = 0

    def __init__(self):
        self._level = 0.0
        self._std = 0.0

    def fit(self, series: pd.Series) -> "HistoricalAverageFallback":
        clean = series.dropna()
        if len(clean) == 0:
            self._level = 0.0
            self._std = 0.0
        else:
            self._level = float(clean.mean())
            self._std = float(clean.std(ddof=1)) if len(clean) > 1 else 0.0
        return self

    def predict(self, horizon: int) -> np.ndarray:
        return np.full(horizon, max(self._level, 0.0))

    def prediction_std(self) -> float:
        return self._std
