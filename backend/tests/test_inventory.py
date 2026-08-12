from datetime import date, timedelta

import pytest

from app.services.inventory_service import (
    compute_overstock_analysis,
    compute_reorder_quantity,
    compute_stockout_prediction,
)
from app.utils import calculations as calc


def _sales_rows(quantity_per_day, days=60):
    return [
        {
            "sale_date": (date.today() - timedelta(days=days - 1 - i)).isoformat(),
            "quantity": quantity_per_day,
            "promotion": False,
        }
        for i in range(days)
    ]


def test_days_of_inventory_zero_demand_returns_none():
    assert calc.days_of_inventory(100, 0) is None


def test_days_of_inventory_basic_math():
    assert calc.days_of_inventory(100, 10) == 10


def test_reorder_point_formula():
    assert calc.reorder_point(lead_time_demand_units=50, safety_stock_units=20) == 70


def test_recommended_order_quantity_never_negative():
    qty = calc.recommended_order_quantity(forecast_demand_units=10, safety_stock_units=5, current_stock=100)
    assert qty == 0


def test_recommended_order_quantity_basic_math():
    qty = calc.recommended_order_quantity(forecast_demand_units=100, safety_stock_units=20, current_stock=50)
    assert qty == 70


def test_classify_stockout_risk_critical_when_within_lead_time():
    assert calc.classify_stockout_risk(days_until_stockout=2, lead_time_days=5) == "CRITICAL"


def test_classify_stockout_risk_low_when_no_stockout_predicted():
    assert calc.classify_stockout_risk(days_until_stockout=None, lead_time_days=5) == "LOW"


def test_classify_stockout_risk_scales_with_lead_time():
    # Same days_until_stockout, different lead times -> different risk.
    # lead=4: 10 days falls within 2x-4x lead time -> MEDIUM.
    # lead=10: 10 days falls within (<=) 1x lead time -> CRITICAL.
    assert calc.classify_stockout_risk(10, lead_time_days=4) == "MEDIUM"
    assert calc.classify_stockout_risk(10, lead_time_days=10) == "CRITICAL"


def test_overstock_detection_flags_excess_and_uses_cost_price():
    result = calc.detect_overstock(current_stock=500, forecast_30_day_demand=120, cost_price=90)
    assert result["overstock"] is True
    assert result["excess_units"] == 380
    assert result["capital_locked"] == 380 * 90


def test_overstock_detection_not_flagged_when_stock_aligned_with_demand():
    result = calc.detect_overstock(current_stock=100, forecast_30_day_demand=120, cost_price=50)
    assert result["overstock"] is False
    assert result["excess_units"] == 0


def test_compute_stockout_prediction_end_to_end_understocked():
    product = {
        "id": "p1",
        "name": "Test Product",
        "current_stock": 5,
        "lead_time_days": 5,
        "safety_stock": 0,
    }
    sales = _sales_rows(quantity_per_day=10, days=30)
    result = compute_stockout_prediction(product, sales)
    assert result["stockout_risk"] in ("CRITICAL", "HIGH")
    assert result["days_until_stockout"] is not None


def test_compute_stockout_prediction_exposes_days_of_inventory():
    product = {
        "id": "p1",
        "name": "Test Product",
        "current_stock": 100,
        "lead_time_days": 5,
        "safety_stock": 0,
    }
    sales = _sales_rows(quantity_per_day=10, days=30)
    result = compute_stockout_prediction(product, sales)
    # current_stock / average_daily_demand == 100 / 10 == 10
    assert result["days_of_inventory"] == pytest.approx(10, abs=0.5)


def test_days_of_inventory_is_none_when_no_demand():
    product = {"id": "p1", "name": "No Demand Product", "current_stock": 50, "lead_time_days": 3, "safety_stock": 0}
    result = compute_stockout_prediction(product, _sales_rows(quantity_per_day=0, days=30))
    assert result["days_of_inventory"] is None


def test_compute_overstock_analysis_end_to_end():
    product = {
        "id": "p1",
        "name": "Test Product",
        "current_stock": 5000,
        "cost_price": 50,
        "lead_time_days": 5,
    }
    sales = _sales_rows(quantity_per_day=2, days=60)
    result = compute_overstock_analysis(product, sales)
    assert result["overstock"] is True
    assert result["capital_locked"] > 0


def test_compute_reorder_quantity_zero_when_well_stocked():
    product = {
        "id": "p1",
        "name": "Test Product",
        "current_stock": 10000,
        "lead_time_days": 3,
        "safety_stock": 10,
    }
    sales = _sales_rows(quantity_per_day=5, days=30)
    qty = compute_reorder_quantity(product, sales)
    assert qty == 0


def test_stockout_prediction_handles_no_sales_history_gracefully():
    product = {"id": "p1", "name": "New Product", "current_stock": 20, "lead_time_days": 3, "safety_stock": 5}
    result = compute_stockout_prediction(product, [])
    assert result["stockout_risk"] == "LOW"
    assert result["average_daily_demand"] == 0
