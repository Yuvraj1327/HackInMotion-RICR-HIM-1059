"""
Base repository class.

All repositories use the service-role Supabase client (so the backend can
perform its own authorization, since we already verified the JWT), but
EVERY query is explicitly filtered by `user_id`. This is deliberate
defense-in-depth: RLS policies (see supabase_schema.sql) enforce the same
isolation at the database level independently, so a bug in either layer
alone still cannot leak data across users.
"""
from typing import Any, Dict, List, Optional

from supabase import Client

from app.database.supabase import get_service_client


class BaseRepository:
    table_name: str = ""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_service_client()

    def _table(self):
        return self.client.table(self.table_name)

    def list_for_user(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        desc: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        query = self._table().select("*").eq("user_id", user_id)
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        if order_by:
            query = query.order(order_by, desc=desc)
        if limit is not None:
            start = offset or 0
            query = query.range(start, start + limit - 1)
        result = query.execute()
        return result.data or []

    def get_by_id(self, user_id: str, record_id: str) -> Optional[Dict[str, Any]]:
        result = (
            self._table()
            .select("*")
            .eq("user_id", user_id)
            .eq("id", record_id)
            .limit(1)
            .execute()
        )
        data = result.data or []
        return data[0] if data else None

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = self._table().insert(payload).execute()
        return result.data[0]

    def update(self, user_id: str, record_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        result = (
            self._table()
            .update(payload)
            .eq("user_id", user_id)
            .eq("id", record_id)
            .execute()
        )
        data = result.data or []
        return data[0] if data else None

    def delete(self, user_id: str, record_id: str) -> bool:
        result = (
            self._table()
            .delete()
            .eq("user_id", user_id)
            .eq("id", record_id)
            .execute()
        )
        return bool(result.data)
