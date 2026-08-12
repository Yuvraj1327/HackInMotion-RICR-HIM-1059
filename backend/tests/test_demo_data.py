import numpy as np

from app.services.demo_data_service import generate_demo_dataset


def test_generates_requested_number_of_products():
    dataset = generate_demo_dataset("user-1", "grocery", days_of_history=90, num_products=18)
    assert len(dataset["products"]) == 18
    assert len(dataset["sales_by_product"]) == 18


def test_generates_suppliers():
    dataset = generate_demo_dataset("user-1", "fashion", days_of_history=90, num_products=20)
    assert 3 <= len(dataset["suppliers"]) <= 5


def test_sales_cover_full_date_range():
    dataset = generate_demo_dataset("user-1", "electronics", days_of_history=120, num_products=15)
    for rows in dataset["sales_by_product"]:
        assert len(rows) == 120


def test_demand_is_not_pure_random_has_weekly_structure():
    """
    A key requirement: demo data must show weekday/weekend structure, not
    just uniform random noise. We check that weekend-average demand differs
    materially from weekday-average demand for a product with a weekend
    multiplier > 1.
    """
    from datetime import date, timedelta

    dataset = generate_demo_dataset("user-1", "grocery", days_of_history=120, num_products=5)
    rows = dataset["sales_by_product"][0]  # Milk 1L, weekend_mult=1.25
    end = date.fromisoformat(dataset["date_range_end"])
    start = date.fromisoformat(dataset["date_range_start"])
    dates = [start + timedelta(days=i) for i in range(len(rows))]

    weekend_qty = [r["quantity"] for r, d in zip(rows, dates) if d.weekday() >= 5]
    weekday_qty = [r["quantity"] for r, d in zip(rows, dates) if d.weekday() < 5]

    assert np.mean(weekend_qty) > np.mean(weekday_qty)


def test_different_products_have_different_demand_profiles():
    dataset = generate_demo_dataset("user-1", "grocery", days_of_history=90, num_products=10)
    avg_demands = [np.mean([r["quantity"] for r in rows]) for rows in dataset["sales_by_product"]]
    # Not all products should have the same average demand (i.e. this
    # isn't just one flat number repeated for every SKU).
    assert len(set(round(a, 1) for a in avg_demands)) > 1


def test_some_promotional_periods_exist():
    dataset = generate_demo_dataset("user-1", "grocery", days_of_history=120, num_products=5)
    any_promo = any(any(r["promotion"] for r in rows) for rows in dataset["sales_by_product"])
    assert any_promo


def test_falls_back_to_grocery_for_unknown_category():
    dataset = generate_demo_dataset("user-1", "unknown-category", days_of_history=90, num_products=5)
    assert len(dataset["products"]) == 5
