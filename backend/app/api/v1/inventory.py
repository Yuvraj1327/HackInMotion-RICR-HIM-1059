from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends

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
from app.database.repositories.products import ProductRepository
from app.database.repositories.sales import SalesRepository
from app.schemas.inventory import OverstockAnalysis, StockoutPrediction
from app.services.inventory_service import compute_overstock_analysis, compute_stockout_prediction
from app.services.sales_series import group_sales_by_product

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/stockout/{product_id}", response_model=StockoutPrediction)
def get_stockout_prediction(
    product_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repository),
    sales_repo: SalesRepository = Depends(get_sales_repository),
):
    product = product_repo.get_by_id(user.id, str(product_id))
    if not product:
        raise NotFoundException("Product not found.")
    sales_rows = sales_repo.list_for_product(user.id, str(product_id))
    result = compute_stockout_prediction(product, sales_rows)
    return {"product_id": product_id, "product_name": product["name"], **result}


@router.get("/stockout", response_model=List[StockoutPrediction])
def list_stockout_predictions(
    user: CurrentUser = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repository),
    sales_repo: SalesRepository = Depends(get_sales_repository),
):
    products = product_repo.list_for_user(user.id)
    # One request for every product's sales instead of one request per
    # product - see dashboard.py for the same fix and why it matters.
    sales_by_product = group_sales_by_product(sales_repo.list_for_user(user.id))
    results = []
    for product in products:
        sales_rows = sales_by_product.get(product["id"], [])
        result = compute_stockout_prediction(product, sales_rows)
        results.append({"product_id": product["id"], "product_name": product["name"], **result})
    return results


@router.get("/overstock/{product_id}", response_model=OverstockAnalysis)
def get_overstock_analysis(
    product_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repository),
    sales_repo: SalesRepository = Depends(get_sales_repository),
):
    product = product_repo.get_by_id(user.id, str(product_id))
    if not product:
        raise NotFoundException("Product not found.")
    sales_rows = sales_repo.list_for_product(user.id, str(product_id))
    result = compute_overstock_analysis(product, sales_rows)
    return {"product_id": product_id, "product_name": product["name"], **result}


@router.get("/overstock", response_model=List[OverstockAnalysis])
def list_overstock_analyses(
    user: CurrentUser = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repository),
    sales_repo: SalesRepository = Depends(get_sales_repository),
):
    products = product_repo.list_for_user(user.id)
    # One request for every product's sales instead of one request per
    # product - see dashboard.py for the same fix and why it matters.
    sales_by_product = group_sales_by_product(sales_repo.list_for_user(user.id))
    results = []
    for product in products:
        sales_rows = sales_by_product.get(product["id"], [])
        result = compute_overstock_analysis(product, sales_rows)
        results.append({"product_id": product["id"], "product_name": product["name"], **result})
    return results