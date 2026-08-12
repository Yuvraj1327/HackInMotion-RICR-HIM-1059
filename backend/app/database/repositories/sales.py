from typing import Any, Dict, List

from app.database.repositories.base import BaseRepository


class SalesRepository(BaseRepository):
    table_name = "sales"

    def list_for_product(self, user_id: str, product_id: str) -> List[Dict[str, Any]]:
        result = (
            self._table()
            .select("*")
            .eq("user_id", user_id)
            .eq("product_id", product_id)
            .order("sale_date")
            .execute()
        )
        return result.data or []

    def bulk_create(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not rows:
            return []
        result = self._table().insert(rows).execute()
        return result.data or []

    def existing_keys_for_product(self, user_id: str, product_id: str) -> set:
        rows = self.list_for_product(user_id, product_id)
        return {(r["product_id"], r["sale_date"]) for r in rows}

    def existing_keys_for_user(self, user_id: str) -> set:
        result = (
            self._table().select("product_id,sale_date").eq("user_id", user_id).execute()
        )
        return {(r["product_id"], r["sale_date"]) for r in (result.data or [])}
