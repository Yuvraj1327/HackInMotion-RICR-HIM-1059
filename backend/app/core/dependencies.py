"""
Reusable FastAPI dependencies, most importantly `get_current_user`.

Every business endpoint depends on `get_current_user`, which:

1. Reads the `Authorization: Bearer <token>` header.
2. Validates the Supabase JWT (signature + expiry).
3. Extracts the user id.
4. Returns a `CurrentUser` object that route handlers use to scope
   every database query to that user only.
"""
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import InvalidTokenException, decode_supabase_jwt
from app.database.repositories.alerts import AlertRepository
from app.database.repositories.forecasts import ForecastRepository, ForecastRunRepository
from app.database.repositories.products import ProductRepository
from app.database.repositories.sales import SalesRepository
from app.database.repositories.suppliers import SupplierRepository

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: str
    email: Optional[str] = None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = decode_supabase_jwt(credentials.credentials)
    except InvalidTokenException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return CurrentUser(id=token_data.user_id, email=token_data.email)


# --------------------------------------------------------------------------
# Repository provider factories.
#
# These are plain functions (not the repository classes themselves) so
# that FastAPI's dependency-injection introspection doesn't try to
# analyze the repository constructor's parameters as request data.
# --------------------------------------------------------------------------
def get_product_repository() -> ProductRepository:
    return ProductRepository()


def get_supplier_repository() -> SupplierRepository:
    return SupplierRepository()


def get_sales_repository() -> SalesRepository:
    return SalesRepository()


def get_forecast_repository() -> ForecastRepository:
    return ForecastRepository()


def get_forecast_run_repository() -> ForecastRunRepository:
    return ForecastRunRepository()


def get_alert_repository() -> AlertRepository:
    return AlertRepository()
