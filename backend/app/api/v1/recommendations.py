from typing import List

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
from app.database.repositories.products import ProductRepository
from app.database.repositories.sales import SalesRepository
from app.schemas.inventory import ReorderRecommendation
from app.services.forecast_service import InsufficientDataError, generate_product_forecast
from app.services.recommendation_service import build_reorder_recommendation, rank_recommendations
from app.services.sales_series import group_sales_by_product

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/reorder", response_model=List[ReorderRecommendation])
def get_reorder_recommendations(
    limit: int = Query(20, ge=1, le=200),
    user: CurrentUser = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repository),
    sales_repo: SalesRepository = Depends(get_sales_repository),
):
    products = product_repo.list_for_user(user.id)
    # One request for every product's sales instead of one request per
    # product - see dashboard.py for the same fix and why it matters.
    sales_by_product = group_sales_by_product(sales_repo.list_for_user(user.id))

    recommendations = []
    for product in products:
        sales_rows = sales_by_product.get(product["id"], [])
        # Fit the demand model once per product and reuse it across the
        # stockout/forecast/reorder-quantity calculations inside
        # build_reorder_recommendation - see dashboard.py for the same
        # optimization and why it matters.
        try:
            forecast_30d = generate_product_forecast(sales_rows, horizon_days=30)
        except InsufficientDataError:
            forecast_30d = None
        try:
            rec = build_reorder_recommendation(product, sales_rows, forecast_30d=forecast_30d)
        except Exception:
            continue
        recommendations.append(rec)

    ranked = rank_recommendations(recommendations)
    # Only surface products that actually need attention or are close to it.
    actionable = [r for r in ranked if r["risk"] in ("CRITICAL", "HIGH", "MEDIUM") or r["recommended_order_quantity"] > 0]
    return actionable[:limit]