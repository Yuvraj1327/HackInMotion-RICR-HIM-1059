"""
High-level forecast generation: takes raw sales rows for a product,
builds the daily series, runs model selection, and returns a structured
forecast result ready for both the API response and for downstream
inventory-risk / alert / recommendation calculations.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.services.forecasting.model_selector import SelectionResult, select_and_forecast
from app.services.sales_series import build_daily_series


class InsufficientDataError(Exception):
    pass


@dataclass
class ProductForecast:
    model_name: str
    points: List[Dict[str, Any]]  # [{date, predicted_demand, lower_bound, upper_bound}]
    confidence: float
    metrics: Optional[Dict[str, float]]
    training_records: int
    notes: Optional[str]

    def total_demand(self, days: Optional[int] = None) -> float:
        pts = self.points[:days] if days else self.points
        return float(sum(p["predicted_demand"] for p in pts))


def generate_product_forecast(
    sales_rows: List[Dict[str, Any]], horizon_days: int
) -> ProductForecast:
    if not sales_rows:
        raise InsufficientDataError("No sales history available for this product.")

    daily_df = build_daily_series(sales_rows)
    if daily_df.empty:
        raise InsufficientDataError("No sales history available for this product.")

    result: SelectionResult = select_and_forecast(daily_df, horizon_days)

    last_date = daily_df["date"].max().date()
    points = []
    for i in range(horizon_days):
        forecast_date = last_date + timedelta(days=i + 1)
        points.append(
            {
                "date": forecast_date,
                "predicted_demand": round(float(result.forecast[i]), 2),
                "lower_bound": round(float(result.lower_bound[i]), 2),
                "upper_bound": round(float(result.upper_bound[i]), 2),
            }
        )

    metrics = None
    if result.metrics:
        metrics = {
            "mae": round(result.metrics.mae, 2),
            "rmse": round(result.metrics.rmse, 2),
            "mape": round(result.metrics.mape, 2),
        }

    return ProductForecast(
        model_name=result.model_name,
        points=points,
        confidence=round(result.confidence, 2),
        metrics=metrics,
        training_records=result.training_records,
        notes=result.notes,
    )
