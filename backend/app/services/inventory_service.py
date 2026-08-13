"""
Inventory risk engine: turns a product's demand forecast + current stock
into stockout risk, overstock analysis, and reorder math. Every number
here traces back to a documented formula in app/utils/calculations.py.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.forecast_service import (
    InsufficientDataError,
    ProductForecast,
    generate_product_forecast,
)
from app.services.sales_series import build_daily_series, recent_window
from app.utils import calculations as calc


def compute_stockout_prediction(
    product: Dict[str, Any],
    sales_rows: List[Dict[str, Any]],
    forecast_30d: Optional[ProductForecast] = None,
) -> Dict[str, Any]:
    """
    `forecast_30d`: an already-computed 30-day forecast for this product,
    if the caller has one on hand (e.g. the dashboard/recommendations
    endpoints, which need the same product's forecast for several
    calculations). When omitted, this generates its own - existing
    callers that only need one calculation are unaffected. Passing a
    forecast computed for a SHORTER horizon than 30 days is not
    supported (the stockout walk needs the full 30-day horizon).
    """
    lead_time_days = int(product.get("lead_time_days") or 0)
    current_stock = float(product.get("current_stock") or 0)

    daily_df = build_daily_series(sales_rows)
    if daily_df.empty:
        avg_demand = 0.0
        demand_std = 0.0
    else:
        window = recent_window(daily_df, 14)
        avg_demand = calc.average_daily_demand(window["quantity"].tolist())
        demand_std = calc.demand_std_dev(window["quantity"].tolist())

    lt_demand = calc.lead_time_demand(avg_demand, lead_time_days)
    safety = float(product.get("safety_stock") or 0) or calc.safety_stock(demand_std, lead_time_days)
    rop = calc.reorder_point(lt_demand, safety)

    stockout_date = None
    days_until_stockout = None
    try:
        forecast = forecast_30d if forecast_30d is not None else generate_product_forecast(sales_rows, horizon_days=30)
        stockout_date, days_until_stockout = calc.estimate_stockout_date(
            current_stock, forecast.points, start_date=forecast.points[0]["date"]
        )
    except InsufficientDataError:
        # Fall back to a simple runway estimate off the recent average
        # when there isn't enough history to run the full forecasting
        # pipeline (e.g. brand-new product).
        doi = calc.days_of_inventory(current_stock, avg_demand)
        if doi is not None:
            days_until_stockout = int(doi)

    risk = calc.classify_stockout_risk(days_until_stockout, lead_time_days)
    days_of_inventory = calc.days_of_inventory(current_stock, avg_demand)

    return {
        "current_stock": int(current_stock),
        "average_daily_demand": round(avg_demand, 2),
        "days_of_inventory": round(days_of_inventory, 1) if days_of_inventory is not None else None,
        "stockout_risk": risk,
        "estimated_stockout_date": stockout_date,
        "days_until_stockout": days_until_stockout,
        "reorder_point": round(rop, 2),
        "lead_time_demand": round(lt_demand, 2),
        "safety_stock": round(safety, 2),
    }


def compute_overstock_analysis(
    product: Dict[str, Any],
    sales_rows: List[Dict[str, Any]],
    forecast_30d: Optional[ProductForecast] = None,
) -> Dict[str, Any]:
    """See `compute_stockout_prediction` for the `forecast_30d` contract."""
    current_stock = float(product.get("current_stock") or 0)
    cost_price = float(product.get("cost_price") or 0)

    try:
        forecast = forecast_30d if forecast_30d is not None else generate_product_forecast(sales_rows, horizon_days=30)
        forecast_30 = forecast.total_demand()
    except InsufficientDataError:
        forecast_30 = 0.0

    result = calc.detect_overstock(current_stock, forecast_30, cost_price)
    result["current_stock"] = int(current_stock)
    result["forecast_30_day_demand"] = round(forecast_30, 2)
    return result


def compute_reorder_quantity(
    product: Dict[str, Any],
    sales_rows: List[Dict[str, Any]],
    horizon_days: int = 14,
    forecast_30d: Optional[ProductForecast] = None,
) -> int:
    """
    See `compute_stockout_prediction` for the `forecast_30d` contract.
    When provided, `forecast_30d` must cover at least `horizon_days` -
    the demand total is taken from its first `horizon_days` points
    (model selection doesn't depend on the requested horizon, so this
    is numerically identical to generating a fresh `horizon_days`
    forecast directly, just without redoing the model fit).
    """
    current_stock = float(product.get("current_stock") or 0)
    lead_time_days = int(product.get("lead_time_days") or 0)

    daily_df = build_daily_series(sales_rows)
    demand_std = 0.0
    if not daily_df.empty:
        window = recent_window(daily_df, 14)
        demand_std = calc.demand_std_dev(window["quantity"].tolist())

    safety = float(product.get("safety_stock") or 0) or calc.safety_stock(demand_std, lead_time_days)

    if forecast_30d is not None:
        forecast_demand = forecast_30d.total_demand(horizon_days)
    else:
        try:
            forecast = generate_product_forecast(sales_rows, horizon_days=horizon_days)
            forecast_demand = forecast.total_demand()
        except InsufficientDataError:
            forecast_demand = 0.0

    return calc.recommended_order_quantity(forecast_demand, safety, current_stock)