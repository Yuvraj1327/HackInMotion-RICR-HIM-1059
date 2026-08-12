"""
Shared interface for all forecasting models plus metric calculations.

Every model consumes a pandas Series of daily demand indexed by date
(continuous daily index, zero-filled for no-sale days) and produces a
horizon of point forecasts. Uncertainty bounds are derived from each
model's own residual/error behaviour, not invented.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class ForecastModel:
    """Abstract base class for all forecasting models."""

    name: str = "base"
    #: minimum number of daily observations this model needs to be usable
    min_observations: int = 1

    def fit(self, series: pd.Series) -> "ForecastModel":
        raise NotImplementedError

    def predict(self, horizon: int) -> np.ndarray:
        """Return an array of `horizon` point forecasts (non-negative)."""
        raise NotImplementedError

    def prediction_std(self) -> float:
        """
        Residual standard deviation from the fit, used to build
        confidence intervals. Subclasses should override with something
        meaningful; default falls back to 0.
        """
        return 0.0

    @classmethod
    def can_use(cls, series: pd.Series) -> bool:
        return len(series.dropna()) >= cls.min_observations


def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def root_mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def mean_absolute_percentage_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    # Avoid divide-by-zero: ignore days with zero actual demand in the
    # MAPE denominator (standard practice), fall back to 0 if all are zero.
    mask = y_true != 0
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def build_confidence_interval(
    point_forecast: np.ndarray, std: float, z_score: float = 1.28
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build symmetric (lower, upper) bounds around point forecasts using a
    Gaussian assumption (z=1.28 -> ~80% interval). Bounds are clipped at
    zero since negative demand is not meaningful.
    """
    margin = z_score * std
    lower = np.clip(point_forecast - margin, 0, None)
    upper = np.clip(point_forecast + margin, 0, None)
    return lower, upper
