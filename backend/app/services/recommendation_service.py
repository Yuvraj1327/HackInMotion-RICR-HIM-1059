"""
Reorder recommendation engine: combines stockout risk + forecast demand
+ reorder math into an explainable, prioritized action list.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.services.forecast_service import InsufficientDataError, generate_product_forecast
from app.services.inventory_service import compute_reorder_quantity, compute_stockout_prediction

_RISK_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def _build_reason(stockout: Dict[str, Any], forecast_7: float, current_stock: float) -> str:
    parts = []
    if stockout["stockout_risk"] in ("CRITICAL", "HIGH"):
        parts.append("current inventory is below the reorder point")
    if forecast_7 > 0 and current_stock < forecast_7:
        parts.append("projected 7-day demand exceeds current stock")
    if not parts:
        parts.append("inventory levels are being monitored against forecast demand")
    return "Recommended because " + " and ".join(parts) + "."


def build_reorder_recommendation(
    product: Dict[str, Any], sales_rows: List[Dict[str, Any]]
) -> Dict[str, Any]:
    stockout = compute_stockout_prediction(product, sales_rows)

    try:
        forecast = generate_product_forecast(sales_rows, horizon_days=7)
        forecast_7 = forecast.total_demand()
    except InsufficientDataError:
        forecast_7 = 0.0

    order_qty = compute_reorder_quantity(product, sales_rows, horizon_days=14)

    return {
        "product_id": product["id"],
        "product_name": product["name"],
        "risk": stockout["stockout_risk"],
        "current_stock": int(product.get("current_stock") or 0),
        "forecast_7_days": round(forecast_7, 2),
        "days_until_stockout": stockout["days_until_stockout"],
        "recommended_order_quantity": order_qty,
        "reason": _build_reason(stockout, forecast_7, float(product.get("current_stock") or 0)),
    }


def rank_recommendations(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort by risk severity, then by soonest stockout, then by largest order quantity."""
    def sort_key(r: Dict[str, Any]):
        risk_rank = _RISK_ORDER.get(r["risk"], 4)
        days = r["days_until_stockout"] if r["days_until_stockout"] is not None else 9999
        return (risk_rank, days, -r["recommended_order_quantity"])

    return sorted(recommendations, key=sort_key)
