#sales_series.py

"""
Turns raw `sales` rows (irregular, one row per transaction/day) into a
continuous daily series with one row per calendar day, zero-filled where
there were no sales. This is the shared input format for both the
forecasting engine and the inventory risk engine.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

import pandas as pd


def build_daily_series(sales_rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    sales_rows: list of dicts with at least `sale_date`, `quantity`,
    `promotion` keys (as returned from the `sales` table).

    Returns a DataFrame with columns [date, quantity, promotion] sorted
    ascending, containing one row per day from the earliest to latest
    sale date (inclusive), zero-filled for days with no recorded sale.
    Promotion is 1 if ANY sale that day was flagged promotional.
    """
    if not sales_rows:
        return pd.DataFrame(columns=["date", "quantity", "promotion"])

    df = pd.DataFrame(sales_rows)
    df["sale_date"] = pd.to_datetime(df["sale_date"]).dt.date
    daily = (
        df.groupby("sale_date")
        .agg(quantity=("quantity", "sum"), promotion=("promotion", "max"))
        .reset_index()
        .rename(columns={"sale_date": "date"})
    )

    start = daily["date"].min()
    end = daily["date"].max()
    full_index = pd.date_range(start, end, freq="D").date
    full = pd.DataFrame({"date": full_index})
    merged = full.merge(daily, on="date", how="left")
    merged["quantity"] = merged["quantity"].fillna(0.0)
    merged["promotion"] = merged["promotion"].fillna(0).astype(int)
    merged["date"] = pd.to_datetime(merged["date"])
    return merged.sort_values("date").reset_index(drop=True)


def recent_window(df: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    if df.empty:
        return df
    return df.tail(days)


def group_sales_by_product(sales_rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Groups a flat list of sales rows (as returned by a single
    `SalesRepository.list_for_user(...)` call covering every product at
    once) into a dict keyed by `product_id`.

    Used by endpoints that need every product's sales history to compute
    dashboard/recommendation/alert data (dashboard, recommendations,
    alerts, inventory list endpoints): fetching once per user and
    grouping in memory replaces what used to be one separate database
    round-trip per product (an N+1 query pattern), while producing
    identical per-product row lists.
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in sales_rows:
        grouped.setdefault(row["product_id"], []).append(row)
    return grouped