from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from app.services.forecasting.base import ForecastModel

FEATURE_COLUMNS = [
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_30",
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_30",
    "day_of_week",
    "day_of_month",
    "month",
    "weekend",
    "promotion",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    df must have columns: date (datetime), quantity (float), promotion (0/1),
    sorted ascending by date, with one row per day (continuous, zero-filled).
    """
    out = df.copy().reset_index(drop=True)
    out["lag_1"] = out["quantity"].shift(1)
    out["lag_7"] = out["quantity"].shift(7)
    out["lag_14"] = out["quantity"].shift(14)
    out["lag_30"] = out["quantity"].shift(30)
    out["rolling_mean_7"] = out["quantity"].shift(1).rolling(7).mean()
    out["rolling_mean_14"] = out["quantity"].shift(1).rolling(14).mean()
    out["rolling_mean_30"] = out["quantity"].shift(1).rolling(30).mean()
    out["day_of_week"] = out["date"].dt.dayofweek
    out["day_of_month"] = out["date"].dt.day
    out["month"] = out["date"].dt.month
    out["weekend"] = (out["date"].dt.dayofweek >= 5).astype(int)
    if "promotion" not in out.columns:
        out["promotion"] = 0
    out["promotion"] = out["promotion"].fillna(0).astype(int)
    return out


class XGBoostForecastModel(ForecastModel):
    """
    Gradient-boosted tree regressor trained on lag/rolling/calendar
    features. Needs meaningfully more history than the statistical
    models (at least ~45 days) so that lag_30 and rolling_mean_30
    features are populated for a reasonable number of training rows.

    Multi-step forecasting is done recursively: each predicted day's
    demand is appended to the history so lag features for the next
    predicted day can be computed.
    """

    name = "XGBoost"
    min_observations = 45

    def __init__(self):
        self.model: XGBRegressor | None = None
        self._history: pd.DataFrame | None = None
        self._resid_std = 0.0

    def fit(self, df: pd.DataFrame) -> "XGBoostForecastModel":
        """df: columns date, quantity, promotion."""
        featured = build_features(df)
        train = featured.dropna(subset=FEATURE_COLUMNS)

        self.model = XGBRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            reg_lambda=1.0,
            objective="reg:squarederror",
        )
        self.model.fit(train[FEATURE_COLUMNS], train["quantity"])

        preds = self.model.predict(train[FEATURE_COLUMNS])
        residuals = train["quantity"].values - preds
        self._resid_std = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0

        self._history = df.copy().reset_index(drop=True)
        return self

    def predict(self, horizon: int) -> np.ndarray:
        assert self.model is not None and self._history is not None
        working = self._history.copy()
        predictions = []

        last_date = working["date"].max()
        for step in range(horizon):
            next_date = last_date + timedelta(days=step + 1)
            new_row = pd.DataFrame(
                [{"date": next_date, "quantity": np.nan, "promotion": 0}]
            )
            combined = pd.concat([working, new_row], ignore_index=True)
            featured = build_features(combined)
            feature_row = featured.iloc[[-1]][FEATURE_COLUMNS].fillna(0)
            pred = float(self.model.predict(feature_row)[0])
            pred = max(pred, 0.0)
            predictions.append(pred)

            working = pd.concat(
                [working, pd.DataFrame([{"date": next_date, "quantity": pred, "promotion": 0}])],
                ignore_index=True,
            )

        return np.array(predictions)

    def prediction_std(self) -> float:
        return self._resid_std
