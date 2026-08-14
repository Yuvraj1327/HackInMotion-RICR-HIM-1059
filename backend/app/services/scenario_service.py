#scenario_service.py


"""
What-if scenario simulator. Re-runs the real forecasting + inventory
calculations under a modified demand and/or supplier lead-time
assumption, so results reflect genuine model behaviour rather than a
canned response.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.services.forecast_service import InsufficientDataError, generate_product_forecast
from app.utils import calculations as calc


def simulate_scenario(
    product: Dict[str, Any],
    sales_rows: List[Dict[str, Any]],
    demand_change_percent: float,
    supplier_delay_days: int,
) -> Dict[str, Any]:
    current_stock = float(product.get("current_stock") or 0)
    base_lead_time = int(product.get("lead_time_days") or 0)
    scenario_lead_time = max(0, base_lead_time + int(supplier_delay_days))

    try:
        forecast = generate_product_forecast(sales_rows, horizon_days=30)
    except InsufficientDataError:
        forecast = None

    if forecast is None:
        baseline_points = []
        scenario_points = []
        baseline_demand_7d = 0.0
        scenario_demand_7d = 0.0
    else:
        baseline_points = forecast.points
        multiplier = 1 + (demand_change_percent / 100.0)
        scenario_points = [
            {
                **p,
                "predicted_demand": round(max(p["predicted_demand"] * multiplier, 0.0), 2),
            }
            for p in baseline_points
        ]
        baseline_demand_7d = sum(p["predicted_demand"] for p in baseline_points[:7])
        scenario_demand_7d = sum(p["predicted_demand"] for p in scenario_points[:7])

    # Baseline stockout
    baseline_stockout_date, baseline_days = calc.estimate_stockout_date(
        current_stock, baseline_points, start_date=baseline_points[0]["date"] if baseline_points else None
    )
    baseline_risk = calc.classify_stockout_risk(baseline_days, base_lead_time)

    # Scenario stockout (uses scenario lead time for risk classification too,
    # since a longer/shorter lead time changes what counts as risky)
    scenario_stockout_date, scenario_days = calc.estimate_stockout_date(
        current_stock, scenario_points, start_date=scenario_points[0]["date"] if scenario_points else None
    )
    scenario_risk = calc.classify_stockout_risk(scenario_days, scenario_lead_time)

    # Safety stock / reorder quantities for both scenarios (14-day horizon)
    safety = float(product.get("safety_stock") or 0)
    baseline_14d = sum(p["predicted_demand"] for p in baseline_points[:14])
    scenario_14d = sum(p["predicted_demand"] for p in scenario_points[:14])

    baseline_order_qty = calc.recommended_order_quantity(baseline_14d, safety, current_stock)
    scenario_order_qty = calc.recommended_order_quantity(scenario_14d, safety, current_stock)

    return {
        "product_id": product["id"],
        "product_name": product["name"],
        "baseline_demand_7d": round(baseline_demand_7d, 2),
        "scenario_demand_7d": round(scenario_demand_7d, 2),
        "baseline_risk": baseline_risk,
        "scenario_risk": scenario_risk,
        "baseline_stockout_date": baseline_stockout_date,
        "scenario_stockout_date": scenario_stockout_date,
        "baseline_days_until_stockout": baseline_days,
        "scenario_days_until_stockout": scenario_days,
        "additional_units_required": max(0, scenario_order_qty - baseline_order_qty),
        "baseline_recommended_order_quantity": baseline_order_qty,
        "scenario_recommended_order_quantity": scenario_order_qty,
    }
