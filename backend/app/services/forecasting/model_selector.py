"""
Model selection pipeline.

For each product:
1. Build a continuous daily demand series (zero-filled for no-sale days).
2. Hold out the last N days as a validation set.
3. Fit every candidate model whose `min_observations` requirement is met
   by the training portion.
4. Score each candidate on the validation set (MAE / RMSE / MAPE).
5. Pick the candidate with the lowest validation MAPE.
6. Refit the winning model type on the FULL series and use it to
   generate the actual future forecast.

If a product has too little data for any statistical/ML candidate, the
`HistoricalAverageFallback` is used and clearly labeled as such.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from app.services.forecasting.base import (
    ForecastModel,
    build_confidence_interval,
    mean_absolute_error,
    mean_absolute_percentage_error,
    root_mean_squared_error,
)
from app.services.forecasting.exponential_smoothing import ExponentialSmoothingModel
from app.services.forecasting.moving_average import (
    HistoricalAverageFallback,
    MovingAverageModel,
)
from app.services.forecasting.xgboost_model import XGBoostForecastModel

MIN_VALIDATION_DAYS = 5
MAX_VALIDATION_DAYS = 14


@dataclass
class ModelCandidateResult:
    name: str
    mae: float
    rmse: float
    mape: float


@dataclass
class SelectionResult:
    model_name: str
    forecast: np.ndarray
    lower_bound: np.ndarray
    upper_bound: np.ndarray
    metrics: Optional[ModelCandidateResult]
    training_records: int
    confidence: float
    notes: Optional[str] = None


def _candidate_classes(uses_dataframe: bool = False):
    return [
        (MovingAverageModel, False),
        (ExponentialSmoothingModel, False),
        (XGBoostForecastModel, True),
    ]


def _validation_window(n: int) -> int:
    window = max(MIN_VALIDATION_DAYS, min(MAX_VALIDATION_DAYS, n // 5))
    return min(window, n - 1) if n > 1 else 0


def _confidence_from_mape(mape: float) -> float:
    """Map validation MAPE to a 0-1 confidence score. Lower error -> higher confidence."""
    if mape is None or np.isnan(mape):
        return 0.5
    confidence = 1 - (mape / 100)
    return float(np.clip(confidence, 0.30, 0.98))


def select_and_forecast(
    df: pd.Series | pd.DataFrame, horizon: int
) -> SelectionResult:
    """
    df: pandas DataFrame with columns [date, quantity, promotion], sorted
    ascending, one row per calendar day (already zero-filled by caller).
    """
    series = df.set_index("date")["quantity"]
    n = len(series)

    # --- Not enough data for anything but a flat historical average ---
    if n < MovingAverageModel.min_observations:
        model = HistoricalAverageFallback().fit(series)
        point = model.predict(horizon)
        std = model.prediction_std()
        lower, upper = build_confidence_interval(point, std)
        return SelectionResult(
            model_name=model.name,
            forecast=point,
            lower_bound=lower,
            upper_bound=upper,
            metrics=None,
            training_records=n,
            confidence=0.35,
            notes=(
                f"Only {n} day(s) of sales history available. Using a flat "
                "historical-average fallback until more data accumulates."
            ),
        )

    val_days = _validation_window(n)
    results: List[ModelCandidateResult] = []
    candidates_tried = []

    if val_days >= 2:
        train_df = df.iloc[: n - val_days]
        val_df = df.iloc[n - val_days :]
        y_true = val_df["quantity"].values

        for model_cls, needs_df in _candidate_classes():
            if len(train_df) < model_cls.min_observations:
                continue
            try:
                model = model_cls()
                if needs_df:
                    model.fit(train_df[["date", "quantity", "promotion"]])
                else:
                    model.fit(train_df.set_index("date")["quantity"])
                y_pred = model.predict(val_days)
                mae = mean_absolute_error(y_true, y_pred)
                rmse = root_mean_squared_error(y_true, y_pred)
                mape = mean_absolute_percentage_error(y_true, y_pred)
                results.append(ModelCandidateResult(model_cls().name, mae, rmse, mape))
                candidates_tried.append(model_cls)
            except Exception:
                # A candidate that fails to fit/predict on this product's
                # data is simply skipped, never crashes the request.
                continue

    if not results:
        # Either too few validation days, or every candidate failed.
        # Fall back to MovingAverage on the full series.
        model = MovingAverageModel().fit(series)
        point = model.predict(horizon)
        std = model.prediction_std()
        lower, upper = build_confidence_interval(point, std)
        return SelectionResult(
            model_name=model.name,
            forecast=point,
            lower_bound=lower,
            upper_bound=upper,
            metrics=None,
            training_records=n,
            confidence=0.45,
            notes="Insufficient data for validation-based model selection; used moving average.",
        )

    # Pick best by MAPE (falls back to RMSE if MAPE ties/degenerate)
    best = min(results, key=lambda r: (r.mape, r.rmse))
    best_cls = next(c for c in candidates_tried if c().name == best.name)

    # Refit the winning model type on the FULL series for the real forecast
    final_model = best_cls()
    if best_cls is XGBoostForecastModel:
        final_model.fit(df[["date", "quantity", "promotion"]])
    else:
        final_model.fit(series)

    point = final_model.predict(horizon)
    std = final_model.prediction_std()
    lower, upper = build_confidence_interval(point, std)
    confidence = _confidence_from_mape(best.mape)

    return SelectionResult(
        model_name=best.name,
        forecast=point,
        lower_bound=lower,
        upper_bound=upper,
        metrics=best,
        training_records=n,
        confidence=confidence,
        notes=f"Selected via validation on last {val_days} day(s); "
        f"compared {len(results)} candidate model(s).",
    )
