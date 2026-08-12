from typing import Any, Dict, List, Optional

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
