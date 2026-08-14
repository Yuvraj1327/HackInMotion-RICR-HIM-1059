from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    get_alert_repository,
    get_current_user,
    get_forecast_repository,
    get_forecast_run_repository,
    get_product_repository,
    get_sales_repository,
    get_supplier_repository,
)
from app.core.exceptions import NotFoundException
from app.database.repositories.alerts import AlertRepository
from app.database.repositories.products import ProductRepository
from app.database.repositories.sales import SalesRepository
from app.schemas.inventory import AlertResponse
from app.schemas.common import MessageResponse
from app.services.alert_service import generate_alerts_for_product
from app.services.sales_series import group_sales_by_product

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _refresh_alerts_for_user(
    user: CurrentUser,
    product_repo: ProductRepository,
    sales_repo: SalesRepository,
    alert_repo: AlertRepository,
) -> None:
    """
    Recomputes alerts from live data for every product and persists any
    newly-detected condition. Existing unresolved alerts of the same
    type for the same product are not duplicated.

    Robustness against alerts.product_id foreign key violations (Postgres
    23503): `products` is fetched once at the top, but this loop can take
    real wall-clock time (forecasting per product), so a product deleted
    concurrently - by the same user in another tab, a fast double
    delete-click, etc. - between that fetch and this specific product's
    turn is a genuine possibility, not just a theoretical one. Two
    independent guards handle it:
      1. Any alert rows already orphaned (referencing a product that no
         longer exists) are cleaned up up front - safe to remove, since
         a deleted product's alerts are meaningless.
      2. Each new-alert insert is wrapped so that if the product was
         deleted in the moment between the fetch above and this
         particular insert, we skip that one alert instead of raising a
         raw database error - we never attempt to create a foreign key
         that isn't valid at insert time.
    """
    products = product_repo.list_for_user(user.id)
    valid_product_ids = {p["id"] for p in products}

    # Remove any pre-existing alerts pointing at a product that no
    # longer belongs to this user (or no longer exists at all) before
    # generating anything new.
    alert_repo.delete_orphaned(user.id, valid_product_ids)

    # One request for every product's sales instead of one request per
    # product - see dashboard.py for the same fix and why it matters.
    sales_by_product = group_sales_by_product(sales_repo.list_for_user(user.id))

    for product in products:
        sales_rows = sales_by_product.get(product["id"], [])
        try:
            new_alerts = generate_alerts_for_product(product, sales_rows)
        except Exception:
            # Never let one product's alert computation break the whole refresh.
            continue

        for alert in new_alerts:
            existing = alert_repo.find_open_duplicate(user.id, alert["product_id"], alert["alert_type"])
            if existing:
                continue
            payload = {**alert, "user_id": user.id, "resolved": False}
            try:
                alert_repo.create(payload)
            except Exception:
                # Most likely cause: the product was deleted in the
                # window between the `list_for_user` call above and this
                # insert, so `product_id` is no longer a valid foreign
                # key. Skip this one alert rather than let a database
                # constraint error surface as a 500 for the whole
                # request - the next refresh will simply not see that
                # product anymore.
                continue


@router.get("", response_model=List[AlertResponse])
def list_alerts(
    resolved: bool = Query(False, description="Include resolved alerts too"),
    limit: int = Query(100, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repository),
    sales_repo: SalesRepository = Depends(get_sales_repository),
    alert_repo: AlertRepository = Depends(get_alert_repository),
):
    _refresh_alerts_for_user(user, product_repo, sales_repo, alert_repo)
    alerts = alert_repo.list_active(user.id, limit=limit)
    if not resolved:
        alerts = [a for a in alerts if not a["resolved"]]
    return alerts


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    alert_repo: AlertRepository = Depends(get_alert_repository),
):
    existing = alert_repo.get_by_id(user.id, str(alert_id))
    if not existing:
        raise NotFoundException("Alert not found.")
    updated = alert_repo.resolve(user.id, str(alert_id))
    return updated