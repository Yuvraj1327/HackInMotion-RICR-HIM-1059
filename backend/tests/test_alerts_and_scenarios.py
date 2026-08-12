from datetime import date, timedelta

from app.services.alert_service import generate_alerts_for_product
from app.services.scenario_service import simulate_scenario


def _sales_rows_pattern(quantities):
    days = len(quantities)
    return [
        {
            "sale_date": (date.today() - timedelta(days=days - 1 - i)).isoformat(),
            "quantity": quantities[i],
            "promotion": False,
        }
        for i in range(days)
    ]


def test_generate_alerts_for_understocked_product_includes_stockout_or_low_stock():
    product = {
        "id": "p1",
        "name": "Understocked Item",
        "current_stock": 3,
        "lead_time_days": 5,
        "safety_stock": 0,
    }
    sales = _sales_rows_pattern([10] * 30)
    alerts = generate_alerts_for_product(product, sales)
    types = {a["alert_type"] for a in alerts}
    assert "STOCKOUT" in types or "LOW_STOCK" in types


def test_generate_alerts_for_overstocked_product_includes_overstock():
    product = {
        "id": "p1",
        "name": "Overstocked Item",
        "current_stock": 5000,
        "cost_price": 50,
        "lead_time_days": 3,
        "safety_stock": 10,
    }
    sales = _sales_rows_pattern([2] * 60)
    alerts = generate_alerts_for_product(product, sales)
    types = {a["alert_type"] for a in alerts}
    assert "OVERSTOCK" in types


def test_demand_spike_alert_triggered_on_sharp_increase():
    product = {"id": "p1", "name": "Spiking Item", "current_stock": 1000, "cost_price": 10, "lead_time_days": 3, "safety_stock": 10}
    # 7 days flat at 10, then last 7 days at 40 (300% increase)
    quantities = [10] * 7 + [40] * 7
    sales = _sales_rows_pattern(quantities)
    alerts = generate_alerts_for_product(product, sales)
    types = {a["alert_type"] for a in alerts}
    assert "DEMAND_SPIKE" in types


def test_alerts_never_crash_on_empty_sales():
    product = {"id": "p1", "name": "No History", "current_stock": 20, "lead_time_days": 3, "safety_stock": 5}
    alerts = generate_alerts_for_product(product, [])
    assert isinstance(alerts, list)


def test_scenario_simulation_increasing_demand_worsens_risk_or_keeps_equal():
    product = {
        "id": "p1",
        "name": "Test Product",
        "current_stock": 50,
        "lead_time_days": 3,
        "safety_stock": 10,
    }
    sales = _sales_rows_pattern([10] * 60)

    result = simulate_scenario(product, sales, demand_change_percent=50, supplier_delay_days=0)
    assert result["scenario_demand_7d"] > result["baseline_demand_7d"]
    # additional units required should be non-negative
    assert result["additional_units_required"] >= 0


def test_scenario_simulation_with_supplier_delay_can_change_risk():
    product = {
        "id": "p1",
        "name": "Test Product",
        "current_stock": 30,
        "lead_time_days": 2,
        "safety_stock": 5,
    }
    sales = _sales_rows_pattern([10] * 60)
    result = simulate_scenario(product, sales, demand_change_percent=0, supplier_delay_days=10)
    assert result["scenario_recommended_order_quantity"] >= result["baseline_recommended_order_quantity"]


def test_scenario_simulation_zero_change_matches_baseline_closely():
    product = {
        "id": "p1",
        "name": "Test Product",
        "current_stock": 30,
        "lead_time_days": 2,
        "safety_stock": 5,
    }
    sales = _sales_rows_pattern([10] * 60)
    result = simulate_scenario(product, sales, demand_change_percent=0, supplier_delay_days=0)
    assert result["baseline_demand_7d"] == result["scenario_demand_7d"]
    assert result["baseline_risk"] == result["scenario_risk"]
