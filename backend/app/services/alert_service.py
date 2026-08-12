"""
Smart alert engine. Generates STOCKOUT / LOW_STOCK / OVERSTOCK /
DEMAND_SPIKE / DEMAND_DROP / DATA_ANOMALY alerts from real calculations
(stockout risk, overstock detection, and period-over-period demand
comparison) - never from arbitrary/random triggers.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from app.services.inventory_service import compute_overstock_analysis, compute_stockout_prediction
from app.services.sales_series import build_daily_series

SPIKE_THRESHOLD_PCT = 50.0   # % increase vs previous comparable period
DROP_THRESHOLD_PCT = -40.0   # % decrease vs previous comparable period
ANOMALY_Z_SCORE = 2.5


def _demand_change_alert(product: Dict[str, Any], sales_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    alerts = []
    daily_df = build_daily_series(sales_rows)
    if len(daily_df) < 14:
        return alerts

    recent = daily_df.tail(7)["quantity"].sum()
    previous = daily_df.tail(14).head(7)["quantity"].sum()

    if previous <= 0:
        return alerts

    pct_change = ((recent - previous) / previous) * 100

    if pct_change >= SPIKE_THRESHOLD_PCT:
        alerts.append(
            {
                "product_id": product["id"],
                "alert_type": "DEMAND_SPIKE",
                "severity": "MEDIUM" if pct_change < 100 else "HIGH",
                "title": f"{product['name']} demand spike",
                "message": (
                    f"{product['name']} demand increased by {pct_change:.0f}% "
                    "over the previous 7-day period."
                ),
                "recommended_action": "Review stock coverage and consider expediting the next reorder.",
            }
        )
    elif pct_change <= DROP_THRESHOLD_PCT:
        alerts.append(
            {
                "product_id": product["id"],
                "alert_type": "DEMAND_DROP",
                "severity": "LOW",
                "title": f"{product['name']} demand drop",
                "message": (
                    f"{product['name']} demand decreased by {abs(pct_change):.0f}% "
                    "over the previous 7-day period."
                ),
                "recommended_action": "Reassess reorder quantities to avoid overstocking.",
            }
        )

    return alerts


def _anomaly_alert(product: Dict[str, Any], sales_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    alerts = []
    daily_df = build_daily_series(sales_rows)
    if len(daily_df) < 15:
        return alerts

    history = daily_df.iloc[:-1]["quantity"]
    today = daily_df.iloc[-1]["quantity"]
    mean = history.mean()
    std = history.std(ddof=1) if len(history) > 1 else 0

    if std <= 0:
        return alerts

    z = (today - mean) / std
    if z >= ANOMALY_Z_SCORE:
        alerts.append(
            {
                "product_id": product["id"],
                "alert_type": "DATA_ANOMALY",
                "severity": "LOW",
                "title": f"Unusual sales activity for {product['name']}",
                "message": (
                    f"Today's sales for {product['name']} ({int(today)} units) are unusually high "
                    f"compared with historical demand (avg {mean:.1f})."
                ),
                "recommended_action": "Verify this is genuine demand and not a data-entry error.",
            }
        )
    return alerts


def generate_alerts_for_product(
    product: Dict[str, Any], sales_rows: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []

    stockout = compute_stockout_prediction(product, sales_rows)
    if stockout["stockout_risk"] in ("CRITICAL", "HIGH"):
        days = stockout["days_until_stockout"]
        alerts.append(
            {
                "product_id": product["id"],
                "alert_type": "STOCKOUT",
                "severity": "CRITICAL" if stockout["stockout_risk"] == "CRITICAL" else "HIGH",
                "title": f"{product['name']} at risk of stockout",
                "message": (
                    f"{product['name']} is predicted to run out in {days} day(s)."
                    if days is not None
                    else f"{product['name']} has very low stock relative to demand."
                ),
                "recommended_action": "Place a reorder now; lead time may not be covered by remaining stock.",
            }
        )
    elif float(product.get("current_stock") or 0) <= stockout["reorder_point"]:
        alerts.append(
            {
                "product_id": product["id"],
                "alert_type": "LOW_STOCK",
                "severity": "MEDIUM",
                "title": f"{product['name']} below reorder point",
                "message": f"{product['name']} is below its calculated reorder point.",
                "recommended_action": "Schedule a reorder soon to avoid future stockout risk.",
            }
        )

    overstock = compute_overstock_analysis(product, sales_rows)
    if overstock["overstock"]:
        alerts.append(
            {
                "product_id": product["id"],
                "alert_type": "OVERSTOCK",
                "severity": "LOW",
                "title": f"{product['name']} overstocked",
                "message": (
                    f"{product['name']} has approximately {int(overstock['excess_units'])} excess units."
                ),
                "recommended_action": overstock["recommendation"],
            }
        )

    alerts.extend(_demand_change_alert(product, sales_rows))
    alerts.extend(_anomaly_alert(product, sales_rows))

    return alerts
