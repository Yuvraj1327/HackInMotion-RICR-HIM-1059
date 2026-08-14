from typing import Any, Dict, List, Optional, Set

from app.database.repositories.base import BaseRepository


class AlertRepository(BaseRepository):
    table_name = "alerts"

    def list_active(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        result = (
            self._table()
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    def find_open_duplicate(
        self, user_id: str, product_id: str, alert_type: str
    ) -> Optional[Dict[str, Any]]:
        result = (
            self._table()
            .select("*")
            .eq("user_id", user_id)
            .eq("product_id", product_id)
            .eq("alert_type", alert_type)
            .eq("resolved", False)
            .limit(1)
            .execute()
        )
        data = result.data or []
        return data[0] if data else None

    def resolve(self, user_id: str, alert_id: str) -> Optional[Dict[str, Any]]:
        return self.update(user_id, alert_id, {"resolved": True})

    def delete_orphaned(self, user_id: str, valid_product_ids: Set[str]) -> int:
        """
        Deletes any alert rows for this user whose product_id is NOT in
        the current set of valid (still-existing) product ids.

        Alerts normally disappear automatically when their product is
        deleted (ON DELETE CASCADE on alerts.product_id in
        supabase_schema.sql), but this is a defensive cleanup for any
        row that slipped through anyway - e.g. a product deleted via a
        path where the cascade didn't apply, or any other drift between
        `alerts` and `products`. Called before generating new alerts so
        the table never accumulates rows referencing a product that no
        longer exists.
        """
        rows = (
            self._table()
            .select("id,product_id")
            .eq("user_id", user_id)
            .execute()
        )
        orphan_ids = [
            r["id"]
            for r in (rows.data or [])
            if r.get("product_id") and r["product_id"] not in valid_product_ids
        ]
        if not orphan_ids:
            return 0
        self._table().delete().in_("id", orphan_ids).execute()
        return len(orphan_ids)