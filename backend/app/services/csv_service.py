"""
CSV import for historical sales data.

Expected columns: date,product_id,quantity,price,promotion

The importer is defensive by design: it never raises on malformed input.
Every row is validated independently; bad rows are collected as
"invalid" with a reason, duplicates are detected and skipped, and the
importer always returns statistics rather than crashing.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple

import pandas as pd

REQUIRED_COLUMNS = {"date", "product_id", "quantity", "price"}


def parse_and_validate_csv(
    file_bytes: bytes,
    valid_product_ids: Set[str],
    existing_keys: Set[Tuple[str, str]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns (valid_rows_ready_for_insert, stats_dict).

    `valid_product_ids`: set of product_id strings that belong to the
    current user (so a CSV can't reference someone else's / a nonexistent
    product).
    `existing_keys`: set of (product_id, date_iso) tuples already present
    in the database, used for duplicate detection alongside in-file dupes.
    """
    warnings: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []
    duplicate_count = 0
    invalid_count = 0

    try:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, keep_default_na=False)
    except Exception as exc:
        return [], {
            "success": False,
            "total_rows": 0,
            "imported_rows": 0,
            "duplicate_rows": 0,
            "invalid_rows": 0,
            "warnings": [{"row": 0, "reason": f"Could not parse CSV file: {exc}"}],
        }

    df.columns = [c.strip().lower() for c in df.columns]
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        return [], {
            "success": False,
            "total_rows": len(df),
            "imported_rows": 0,
            "duplicate_rows": 0,
            "invalid_rows": len(df),
            "warnings": [
                {
                    "row": 0,
                    "reason": f"Missing required column(s): {', '.join(sorted(missing_cols))}",
                }
            ],
        }

    seen_in_file: Set[Tuple[str, str]] = set()
    total_rows = len(df)

    for idx, row in df.iterrows():
        row_num = idx + 2  # +1 for 0-index, +1 for header row
        try:
            product_id = str(row["product_id"]).strip()
            if not product_id:
                raise ValueError("product_id is empty")
            if product_id not in valid_product_ids:
                raise ValueError(f"product_id '{product_id}' does not belong to this user")

            raw_date = str(row["date"]).strip()
            parsed_date = pd.to_datetime(raw_date, errors="raise").date()

            quantity_raw = str(row["quantity"]).strip()
            if quantity_raw == "":
                raise ValueError("quantity is missing")
            quantity = float(quantity_raw)
            if quantity < 0:
                raise ValueError("quantity cannot be negative")

            price_raw = str(row["price"]).strip()
            price = float(price_raw) if price_raw != "" else 0.0
            if price < 0:
                raise ValueError("price cannot be negative")

            promotion_raw = str(row.get("promotion", "0")).strip()
            promotion = promotion_raw not in ("", "0", "0.0", "false", "False", "FALSE")

            key = (product_id, parsed_date.isoformat())
            if key in seen_in_file or key in existing_keys:
                duplicate_count += 1
                continue
            seen_in_file.add(key)

            valid_rows.append(
                {
                    "product_id": product_id,
                    "sale_date": parsed_date.isoformat(),
                    "quantity": int(round(quantity)),
                    "unit_price": price,
                    "promotion": promotion,
                }
            )
        except Exception as exc:
            invalid_count += 1
            if len(warnings) < 50:  # cap warnings so huge bad files don't balloon the response
                warnings.append({"row": row_num, "reason": str(exc)})

    return valid_rows, {
        "success": True,
        "total_rows": total_rows,
        "imported_rows": len(valid_rows),
        "duplicate_rows": duplicate_count,
        "invalid_rows": invalid_count,
        "warnings": warnings,
    }
