"""
Core inventory math. Every formula here is documented so the numbers the
API returns are explainable, not "AI magic".

References: these are standard inventory-management formulas used in
retail/supply-chain operations (see README.md section "Inventory
Formulas" for the full writeup with citations).
"""
from datetime import date, timedelta
from typing import List, Optional, Sequence

import numpy as np

Z_SCORE_95 = 1.65  # one-sided 95% service level


def average_daily_demand(recent_quantities: Sequence[float]) -> float:
    """
    Mean units sold per day over a recent lookback window (typically the
    last 14-30 days of actual sales, zero-filled for days with no sale).
    """
    if not recent_quantities:
        return 0.0
    return float(np.mean(recent_quantities))


def demand_std_dev(recent_quantities: Sequence[float]) -> float:
    """Sample standard deviation of daily demand, used for safety stock."""
    if len(recent_quantities) < 2:
        return 0.0
    return float(np.std(recent_quantities, ddof=1))


def days_of_inventory(current_stock: float, avg_daily_demand: float) -> Optional[float]:
    """
    current_stock / average_daily_demand

    Returns None (i.e. "infinite" runway) when there is no measurable
    demand, since division by zero has no meaningful business answer.
    """
    if avg_daily_demand <= 0:
        return None
    return current_stock / avg_daily_demand


def lead_time_demand(avg_daily_demand: float, lead_time_days: int) -> float:
    """Expected units that will be sold while waiting for a reorder to arrive."""
    return avg_daily_demand * lead_time_days


def safety_stock(
    demand_std: float,
    lead_time_days: int,
    z_score: float = Z_SCORE_95,
) -> float:
    """
    Safety Stock = Z * demand_std_dev * sqrt(lead_time_days)

    This is the standard statistical safety-stock formula that buffers
    against demand variability during the lead time window, targeting a
    ~95% service level (Z=1.65) by default. If a product-level
    `safety_stock` override was configured manually by the user, callers
    should prefer that value instead of this calculated one.
    """
    if lead_time_days <= 0:
        return 0.0
    return z_score * demand_std * (lead_time_days ** 0.5)


def reorder_point(lead_time_demand_units: float, safety_stock_units: float) -> float:
    """Reorder Point = Lead-Time Demand + Safety Stock."""
    return lead_time_demand_units + safety_stock_units


def recommended_order_quantity(
    forecast_demand_units: float,
    safety_stock_units: float,
    current_stock: float,
) -> int:
    """
    Recommended Order Qty = forecast_demand + safety_stock - current_stock

    Never negative: if current stock already covers forecast demand plus
    the safety buffer, no reorder is needed.
    """
    qty = forecast_demand_units + safety_stock_units - current_stock
    return max(0, round(qty))


def estimate_stockout_date(
    current_stock: float,
    forecast_points: Sequence[dict],
    start_date: date,
) -> tuple[Optional[date], Optional[int]]:
    """
    Walk forward day-by-day through the forecast, subtracting predicted
    demand from current stock, until stock reaches zero or the forecast
    horizon is exhausted.

    `forecast_points` is a list of dicts with keys `date` (date) and
    `predicted_demand` (float), in chronological order.

    Returns (estimated_stockout_date, days_until_stockout) or (None, None)
    if stock does not run out within the forecast horizon.
    """
    remaining = current_stock
    for i, point in enumerate(forecast_points, start=1):
        remaining -= point["predicted_demand"]
        if remaining <= 0:
            return point["date"], i
    return None, None


def classify_stockout_risk(
    days_until_stockout: Optional[int],
    lead_time_days: int,
) -> str:
    """
    Risk classification is relative to the supplier's lead time, not an
    arbitrary fixed day count:

    - CRITICAL: stock runs out before or during the lead time window
                (a reorder placed today would arrive too late).
    - HIGH:     stock runs out within 2x the lead time.
    - MEDIUM:   stock runs out within 4x the lead time.
    - LOW:      stock runway exceeds 4x the lead time, or no stockout
                predicted within the forecast horizon at all.
    """
    if days_until_stockout is None:
        return "LOW"

    lead = max(lead_time_days, 1)
    if days_until_stockout <= lead:
        return "CRITICAL"
    if days_until_stockout <= lead * 2:
        return "HIGH"
    if days_until_stockout <= lead * 4:
        return "MEDIUM"
    return "LOW"


def detect_overstock(
    current_stock: float,
    forecast_30_day_demand: float,
    cost_price: float,
    overstock_threshold_ratio: float = 1.5,
) -> dict:
    """
    A product is flagged as overstocked when current stock exceeds the
    30-day forecast demand by more than `overstock_threshold_ratio`
    (default 1.5x -> more than 50% excess coverage).

    capital_locked = excess_units * cost_price (cost price, not selling
    price, since that is the actual capital tied up).
    """
    threshold = forecast_30_day_demand * overstock_threshold_ratio
    is_overstock = current_stock > threshold and current_stock > 0
    excess_units = max(0.0, current_stock - forecast_30_day_demand) if is_overstock else 0.0
    capital_locked = excess_units * cost_price

    if is_overstock:
        recommendation = (
            "Consider promotional pricing, bundling, or clearance to reduce "
            "excess inventory and free up locked capital."
        )
    else:
        recommendation = "Stock levels are aligned with forecast demand."

    return {
        "overstock": is_overstock,
        "excess_units": round(excess_units, 2),
        "capital_locked": round(capital_locked, 2),
        "recommendation": recommendation,
    }
