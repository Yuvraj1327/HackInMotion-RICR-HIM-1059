"""
Realistic synthetic demo-data generator.

Businesses evaluating StockPilot AI at a hackathon demo may not have
real historical sales data on hand. This generator produces plausible
product catalogs, suppliers, and daily sales history that exhibit the
kind of structure real retail demand has: weekday/weekend variation,
gentle trend, seasonality, promotional lifts, occasional spikes/drops,
and per-product differences (e.g. Milk behaves very differently from a
Bluetooth Speaker) - NOT uniform random noise.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any, Dict, List

import numpy as np

# Each product template: (name, category_tag, base_daily_demand, price,
# cost_ratio, weekend_multiplier, volatility)
# weekend_multiplier > 1 means demand rises on weekends (Sat/Sun),
# < 1 means it falls (e.g. B2B/office supplies).
PRODUCT_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "grocery": [
        {"name": "Milk 1L", "base": 45, "price": 65, "cost_ratio": 0.77, "weekend_mult": 1.25, "vol": 0.15},
        {"name": "Brown Bread 400g", "base": 30, "price": 45, "cost_ratio": 0.70, "weekend_mult": 1.15, "vol": 0.15},
        {"name": "Farm Eggs (12 pack)", "base": 25, "price": 90, "cost_ratio": 0.72, "weekend_mult": 1.2, "vol": 0.18},
        {"name": "Basmati Rice 5kg", "base": 12, "price": 480, "cost_ratio": 0.80, "weekend_mult": 1.05, "vol": 0.20},
        {"name": "Toor Dal 1kg", "base": 15, "price": 160, "cost_ratio": 0.78, "weekend_mult": 1.05, "vol": 0.18},
        {"name": "Sunflower Oil 1L", "base": 18, "price": 175, "cost_ratio": 0.85, "weekend_mult": 1.1, "vol": 0.20},
        {"name": "Cold Drinks 750ml", "base": 40, "price": 45, "cost_ratio": 0.60, "weekend_mult": 1.6, "vol": 0.35},
        {"name": "Potato Chips Family Pack", "base": 22, "price": 60, "cost_ratio": 0.55, "weekend_mult": 1.4, "vol": 0.30},
        {"name": "Fresh Tomatoes (kg)", "base": 35, "price": 40, "cost_ratio": 0.65, "weekend_mult": 1.1, "vol": 0.30},
        {"name": "Onions (kg)", "base": 38, "price": 35, "cost_ratio": 0.65, "weekend_mult": 1.1, "vol": 0.28},
        {"name": "Bananas (dozen)", "base": 28, "price": 55, "cost_ratio": 0.68, "weekend_mult": 1.15, "vol": 0.22},
        {"name": "Paneer 200g", "base": 20, "price": 85, "cost_ratio": 0.72, "weekend_mult": 1.3, "vol": 0.22},
        {"name": "Curd 400g", "base": 26, "price": 40, "cost_ratio": 0.70, "weekend_mult": 1.2, "vol": 0.18},
        {"name": "Tea Powder 500g", "base": 10, "price": 220, "cost_ratio": 0.75, "weekend_mult": 1.0, "vol": 0.15},
        {"name": "Instant Noodles (pack of 6)", "base": 24, "price": 72, "cost_ratio": 0.60, "weekend_mult": 1.25, "vol": 0.25},
        {"name": "Detergent Powder 1kg", "base": 9, "price": 140, "cost_ratio": 0.78, "weekend_mult": 1.0, "vol": 0.18},
        {"name": "Toothpaste 150g", "base": 11, "price": 95, "cost_ratio": 0.70, "weekend_mult": 1.0, "vol": 0.15},
        {"name": "Biscuits Family Pack", "base": 27, "price": 50, "cost_ratio": 0.58, "weekend_mult": 1.3, "vol": 0.25},
        {"name": "Frozen Peas 500g", "base": 13, "price": 65, "cost_ratio": 0.68, "weekend_mult": 1.1, "vol": 0.20},
        {"name": "Ghee 500ml", "base": 7, "price": 320, "cost_ratio": 0.80, "weekend_mult": 1.05, "vol": 0.20},
        {"name": "Namkeen Mix 400g", "base": 18, "price": 80, "cost_ratio": 0.60, "weekend_mult": 1.35, "vol": 0.28},
    ],
    "fashion": [
        {"name": "Men's Cotton T-Shirt", "base": 14, "price": 599, "cost_ratio": 0.45, "weekend_mult": 1.5, "vol": 0.30},
        {"name": "Women's Kurti", "base": 12, "price": 799, "cost_ratio": 0.42, "weekend_mult": 1.5, "vol": 0.32},
        {"name": "Denim Jeans", "base": 9, "price": 1499, "cost_ratio": 0.48, "weekend_mult": 1.6, "vol": 0.28},
        {"name": "Formal Shirt", "base": 8, "price": 999, "cost_ratio": 0.45, "weekend_mult": 1.3, "vol": 0.25},
        {"name": "Sports Shoes", "base": 7, "price": 2499, "cost_ratio": 0.50, "weekend_mult": 1.6, "vol": 0.30},
        {"name": "Casual Sneakers", "base": 8, "price": 1799, "cost_ratio": 0.48, "weekend_mult": 1.5, "vol": 0.30},
        {"name": "Leather Wallet", "base": 6, "price": 699, "cost_ratio": 0.40, "weekend_mult": 1.3, "vol": 0.25},
        {"name": "Ladies Handbag", "base": 6, "price": 1299, "cost_ratio": 0.42, "weekend_mult": 1.5, "vol": 0.30},
        {"name": "Ethnic Saree", "base": 5, "price": 1999, "cost_ratio": 0.45, "weekend_mult": 1.4, "vol": 0.35},
        {"name": "Kids T-Shirt", "base": 10, "price": 399, "cost_ratio": 0.45, "weekend_mult": 1.5, "vol": 0.28},
        {"name": "Winter Jacket", "base": 4, "price": 2199, "cost_ratio": 0.50, "weekend_mult": 1.4, "vol": 0.40},
        {"name": "Sports Track Pants", "base": 9, "price": 899, "cost_ratio": 0.46, "weekend_mult": 1.4, "vol": 0.25},
        {"name": "Sunglasses", "base": 7, "price": 799, "cost_ratio": 0.35, "weekend_mult": 1.5, "vol": 0.30},
        {"name": "Formal Trousers", "base": 6, "price": 1199, "cost_ratio": 0.46, "weekend_mult": 1.2, "vol": 0.22},
        {"name": "Cotton Saree", "base": 5, "price": 1499, "cost_ratio": 0.44, "weekend_mult": 1.3, "vol": 0.30},
        {"name": "Analog Wrist Watch", "base": 5, "price": 1599, "cost_ratio": 0.40, "weekend_mult": 1.3, "vol": 0.28},
        {"name": "Baseball Cap", "base": 11, "price": 349, "cost_ratio": 0.35, "weekend_mult": 1.4, "vol": 0.30},
        {"name": "Cotton Socks (3-pack)", "base": 15, "price": 249, "cost_ratio": 0.40, "weekend_mult": 1.1, "vol": 0.18},
    ],
    "electronics": [
        {"name": "Bluetooth Speaker", "base": 6, "price": 1999, "cost_ratio": 0.55, "weekend_mult": 1.4, "vol": 0.30},
        {"name": "Wireless Earbuds", "base": 9, "price": 1499, "cost_ratio": 0.50, "weekend_mult": 1.3, "vol": 0.28},
        {"name": "Power Bank 10000mAh", "base": 8, "price": 999, "cost_ratio": 0.55, "weekend_mult": 1.2, "vol": 0.22},
        {"name": "USB-C Cable", "base": 20, "price": 199, "cost_ratio": 0.45, "weekend_mult": 1.1, "vol": 0.20},
        {"name": "Smartphone Charger 20W", "base": 12, "price": 599, "cost_ratio": 0.50, "weekend_mult": 1.15, "vol": 0.20},
        {"name": "Smart Watch", "base": 5, "price": 3499, "cost_ratio": 0.55, "weekend_mult": 1.3, "vol": 0.32},
        {"name": "LED Desk Lamp", "base": 6, "price": 799, "cost_ratio": 0.50, "weekend_mult": 1.1, "vol": 0.20},
        {"name": "Laptop Cooling Pad", "base": 4, "price": 999, "cost_ratio": 0.55, "weekend_mult": 1.1, "vol": 0.18},
        {"name": "Wired Headphones", "base": 10, "price": 399, "cost_ratio": 0.48, "weekend_mult": 1.2, "vol": 0.22},
        {"name": "HDMI Cable 2m", "base": 9, "price": 349, "cost_ratio": 0.45, "weekend_mult": 1.05, "vol": 0.18},
        {"name": "Mechanical Keyboard", "base": 4, "price": 2999, "cost_ratio": 0.55, "weekend_mult": 1.25, "vol": 0.28},
        {"name": "Wireless Mouse", "base": 11, "price": 599, "cost_ratio": 0.48, "weekend_mult": 1.15, "vol": 0.20},
        {"name": "32GB Pendrive", "base": 15, "price": 449, "cost_ratio": 0.50, "weekend_mult": 1.05, "vol": 0.18},
        {"name": "Portable SSD 512GB", "base": 3, "price": 4499, "cost_ratio": 0.60, "weekend_mult": 1.1, "vol": 0.25},
        {"name": "Router Wi-Fi 6", "base": 3, "price": 2799, "cost_ratio": 0.58, "weekend_mult": 1.05, "vol": 0.20},
        {"name": "Webcam 1080p", "base": 4, "price": 1299, "cost_ratio": 0.52, "weekend_mult": 1.1, "vol": 0.22},
    ],
    "cosmetics": [
        {"name": "Face Wash 100ml", "base": 16, "price": 199, "cost_ratio": 0.42, "weekend_mult": 1.1, "vol": 0.20},
        {"name": "Sunscreen SPF50", "base": 14, "price": 349, "cost_ratio": 0.40, "weekend_mult": 1.1, "vol": 0.22},
        {"name": "Matte Lipstick", "base": 12, "price": 449, "cost_ratio": 0.35, "weekend_mult": 1.35, "vol": 0.30},
        {"name": "Foundation 30ml", "base": 8, "price": 699, "cost_ratio": 0.38, "weekend_mult": 1.3, "vol": 0.28},
        {"name": "Shampoo 340ml", "base": 15, "price": 299, "cost_ratio": 0.45, "weekend_mult": 1.1, "vol": 0.18},
        {"name": "Conditioner 340ml", "base": 12, "price": 319, "cost_ratio": 0.45, "weekend_mult": 1.1, "vol": 0.18},
        {"name": "Face Moisturizer 50g", "base": 13, "price": 399, "cost_ratio": 0.40, "weekend_mult": 1.15, "vol": 0.20},
        {"name": "Kajal / Eyeliner", "base": 17, "price": 199, "cost_ratio": 0.32, "weekend_mult": 1.3, "vol": 0.25},
        {"name": "Perfume 100ml", "base": 6, "price": 1299, "cost_ratio": 0.35, "weekend_mult": 1.4, "vol": 0.32},
        {"name": "Body Lotion 400ml", "base": 11, "price": 349, "cost_ratio": 0.42, "weekend_mult": 1.1, "vol": 0.18},
        {"name": "Hair Serum 100ml", "base": 9, "price": 449, "cost_ratio": 0.40, "weekend_mult": 1.15, "vol": 0.20},
        {"name": "Nail Polish", "base": 14, "price": 149, "cost_ratio": 0.30, "weekend_mult": 1.3, "vol": 0.28},
        {"name": "Face Serum 30ml", "base": 7, "price": 899, "cost_ratio": 0.38, "weekend_mult": 1.2, "vol": 0.25},
        {"name": "BB Cream 30g", "base": 8, "price": 549, "cost_ratio": 0.38, "weekend_mult": 1.25, "vol": 0.25},
        {"name": "Herbal Soap Bar", "base": 20, "price": 89, "cost_ratio": 0.45, "weekend_mult": 1.05, "vol": 0.15},
        {"name": "Talcum Powder 400g", "base": 12, "price": 179, "cost_ratio": 0.42, "weekend_mult": 1.0, "vol": 0.15},
    ],
}

SUPPLIER_NAME_POOL = [
    "Metro Distributors", "Bhopal Wholesale Traders", "Central India Suppliers Pvt Ltd",
    "Prime Logistics & Supply", "National Trade Partners", "Star Distribution Co.",
    "Vindhya Traders", "Rapid Supply Chain Solutions",
]

# Festival-ish demand-lift windows within the generated period are applied
# generically as "promotional periods" rather than hardcoded festival dates,
# keeping this reusable regardless of which months the demo happens to cover.


def _generate_supplier(user_id: str) -> Dict[str, Any]:
    name = random.choice(SUPPLIER_NAME_POOL)
    lead_time = random.choice([2, 3, 4, 5, 7])
    return {
        "user_id": user_id,
        "name": name,
        "contact_name": random.choice(["Rahul Sharma", "Priya Verma", "Amit Singh", "Sneha Joshi", "Vikram Rao"]),
        "email": f"contact@{name.lower().replace(' ', '').replace('.', '').replace('&', 'and')[:15]}.com",
        "phone": f"+91-{random.randint(7000000000, 9999999999)}",
        "lead_time_days": lead_time,
        "reliability_score": round(random.uniform(0.82, 0.99), 2),
    }


def _generate_daily_demand(
    base: float,
    weekend_mult: float,
    volatility: float,
    days: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns (quantities, promotion_flags) arrays of length `days`,
    representing a realistic demand curve ending "today" (i.e. index
    days-1 is yesterday relative to when forecasting will run).
    """
    day_indices = np.arange(days)

    # Gentle linear trend: total drift over the period is +-(10-25%) of base
    trend_pct = rng.uniform(-0.20, 0.25)
    trend = base * trend_pct * (day_indices / max(days - 1, 1))

    # Seasonality: slow sine wave (roughly a ~45-90 day cycle) for gradual
    # ebb and flow, e.g. mimicking broader seasonal shifts in a quarter.
    season_period = rng.uniform(45, 90)
    season_amplitude = base * rng.uniform(0.05, 0.15)
    seasonality = season_amplitude * np.sin(2 * np.pi * day_indices / season_period)

    # Weekly pattern
    dates = [date.today() - timedelta(days=(days - 1 - i)) for i in range(days)]
    weekday_mult = np.array([weekend_mult if d.weekday() >= 5 else 1.0 for d in dates])

    level = np.clip(base + trend + seasonality, a_min=base * 0.15, a_max=None) * weekday_mult

    # Promotional periods: 1-3 random windows of 2-5 days with a demand lift
    promotion_flags = np.zeros(days, dtype=int)
    num_promos = rng.integers(1, 4)
    for _ in range(num_promos):
        start = rng.integers(0, max(days - 5, 1))
        length = rng.integers(2, 6)
        end = min(start + length, days)
        promotion_flags[start:end] = 1
        level[start:end] *= rng.uniform(1.4, 1.9)

    # Occasional demand spikes (viral moment / bulk order) and drops
    # (competitor promo, temporary disinterest)
    num_spikes = rng.integers(1, 3)
    for _ in range(num_spikes):
        idx = rng.integers(0, days)
        level[idx] *= rng.uniform(2.0, 3.2)

    num_drops = rng.integers(1, 3)
    for _ in range(num_drops):
        idx = rng.integers(0, days)
        level[idx] *= rng.uniform(0.1, 0.4)

    # Random noise (Poisson-like via gaussian around level, scaled by volatility)
    noise_std = np.maximum(level * volatility, 0.5)
    noisy = rng.normal(level, noise_std)
    quantities = np.clip(np.round(noisy), 0, None).astype(int)

    return quantities, promotion_flags


def generate_demo_dataset(
    user_id: str,
    business_category: str,
    days_of_history: int,
    num_products: int,
) -> Dict[str, Any]:
    """
    Returns a dict with keys: suppliers (list, no ids yet), products
    (list, no ids/supplier_id resolved yet - caller assigns after
    inserting suppliers), sales_by_product_index (list of list-of-dicts
    aligned to `products`), and date range metadata.
    """
    templates = PRODUCT_TEMPLATES.get(business_category, PRODUCT_TEMPLATES["grocery"])
    chosen = templates[: min(num_products, len(templates))]
    # If num_products > available templates, allow repeats with slight name suffixes
    while len(chosen) < num_products:
        extra = random.choice(templates)
        chosen.append(extra)

    num_suppliers = max(3, min(5, num_products // 4))
    suppliers = [_generate_supplier(user_id) for _ in range(num_suppliers)]

    end_date = date.today() - timedelta(days=1)  # yesterday, so forecasts start "today"
    start_date = end_date - timedelta(days=days_of_history - 1)

    products: List[Dict[str, Any]] = []
    sales_by_product: List[List[Dict[str, Any]]] = []

    for i, tmpl in enumerate(chosen):
        rng = np.random.default_rng(seed=hash((tmpl["name"], i, business_category)) % (2**32))
        quantities, promo_flags = _generate_daily_demand(
            base=tmpl["base"],
            weekend_mult=tmpl["weekend_mult"],
            volatility=tmpl["vol"],
            days=days_of_history,
            rng=rng,
        )

        avg_recent_demand = float(np.mean(quantities[-14:])) if days_of_history >= 14 else float(np.mean(quantities))
        lead_time_days = suppliers[i % num_suppliers]["lead_time_days"]

        # Deliberately vary stock posture across products so the demo
        # showcases stockout risk AND overstock scenarios, not just
        # "everything is fine".
        posture = rng.choice(["understocked", "balanced", "balanced", "overstocked"])
        if posture == "understocked":
            current_stock = int(round(avg_recent_demand * rng.uniform(0.5, lead_time_days * 0.8 + 1)))
        elif posture == "overstocked":
            current_stock = int(round(avg_recent_demand * rng.uniform(35, 60)))
        else:
            current_stock = int(round(avg_recent_demand * rng.uniform(8, 18)))
        current_stock = max(current_stock, 0)

        cost_price = round(tmpl["price"] * tmpl["cost_ratio"], 2)
        sku = f"{business_category[:3].upper()}{i+1:03d}"

        products.append(
            {
                "user_id": user_id,
                "name": tmpl["name"],
                "sku": sku,
                "category": business_category,
                "current_stock": current_stock,
                "price": tmpl["price"],
                "cost_price": cost_price,
                "lead_time_days": lead_time_days,
                "safety_stock": int(round(avg_recent_demand * rng.uniform(1.5, 3))),
                "unit": "unit",
                "_supplier_index": i % num_suppliers,
            }
        )

        dates = [start_date + timedelta(days=d) for d in range(days_of_history)]
        rows = [
            {
                "sale_date": dates[d].isoformat(),
                "quantity": int(quantities[d]),
                "unit_price": tmpl["price"],
                "promotion": bool(promo_flags[d]),
            }
            for d in range(days_of_history)
        ]
        sales_by_product.append(rows)

    return {
        "suppliers": suppliers,
        "products": products,
        "sales_by_product": sales_by_product,
        "date_range_start": start_date.isoformat(),
        "date_range_end": end_date.isoformat(),
    }
