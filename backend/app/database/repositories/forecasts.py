from typing import Any, Dict, List

from app.database.repositories.base import BaseRepository


class ForecastRepository(BaseRepository):
    table_name = "forecasts"

    def list_for_product(self, user_id: str, product_id: str) -> List[Dict[str, Any]]:
        result = (
            self._table()
            .select("*")
            .eq("user_id", user_id)
            .eq("product_id", product_id)
            .order("forecast_date")
            .execute()
        )
        return result.data or []

    def bulk_create(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not rows:
            return []
        result = self._table().insert(rows).execute()
        return result.data or []

    def delete_for_product(self, user_id: str, product_id: str) -> None:
        self._table().delete().eq("user_id", user_id).eq("product_id", product_id).execute()


class ForecastRunRepository(BaseRepository):
    table_name = "forecast_runs"
