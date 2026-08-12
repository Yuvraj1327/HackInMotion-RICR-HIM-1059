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
from app.core.exceptions import InsufficientDataException, NotFoundException
from app.database.repositories.forecasts import ForecastRepository, ForecastRunRepository
from app.database.repositories.products import ProductRepository
from app.database.repositories.sales import SalesRepository
from app.schemas.forecast import (
    ForecastGenerateRequest,
    ForecastGenerateResponse,
    ForecastMetrics,
    ForecastPoint,
    ForecastRecord,
)
from app.services.forecast_service import InsufficientDataError, generate_product_forecast

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


@router.post("/generate/{product_id}", response_model=ForecastGenerateResponse)
def generate_forecast(
    product_id: UUID,
    payload: ForecastGenerateRequest,
    user: CurrentUser = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repository),
    sales_repo: SalesRepository = Depends(get_sales_repository),
    forecast_repo: ForecastRepository = Depends(get_forecast_repository),
    run_repo: ForecastRunRepository = Depends(get_forecast_run_repository),
):
    product = product_repo.get_by_id(user.id, str(product_id))
    if not product:
        raise NotFoundException("Product not found.")

    sales_rows = sales_repo.list_for_product(user.id, str(product_id))

    try:
        result = generate_product_forecast(sales_rows, payload.horizon_days)
    except InsufficientDataError as exc:
        raise InsufficientDataException(str(exc))

    # Persist: replace any previously stored forecast rows for this product
    forecast_repo.delete_for_product(user.id, str(product_id))
    forecast_rows = [
        {
            "user_id": user.id,
            "product_id": str(product_id),
            "forecast_date": p["date"].isoformat(),
            "predicted_demand": p["predicted_demand"],
            "lower_bound": p["lower_bound"],
            "upper_bound": p["upper_bound"],
            "model_name": result.model_name,
            "confidence": result.confidence,
        }
        for p in result.points
    ]
    forecast_repo.bulk_create(forecast_rows)

    run_repo.create(
        {
            "user_id": user.id,
            "product_id": str(product_id),
            "model_name": result.model_name,
            "training_records": result.training_records,
            "forecast_horizon": payload.horizon_days,
            "mae": result.metrics["mae"] if result.metrics else None,
            "rmse": result.metrics["rmse"] if result.metrics else None,
            "mape": result.metrics["mape"] if result.metrics else None,
        }
    )

    return ForecastGenerateResponse(
        product_id=product_id,
        product_name=product["name"],
        model=result.model_name,
        forecast=[ForecastPoint(**p) for p in result.points],
        confidence=result.confidence,
        metrics=ForecastMetrics(**(result.metrics or {})),
        training_records=result.training_records,
        notes=result.notes,
    )


@router.get("/{product_id}", response_model=List[ForecastRecord])
def get_forecast_for_product(
    product_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repository),
    forecast_repo: ForecastRepository = Depends(get_forecast_repository),
):
    product = product_repo.get_by_id(user.id, str(product_id))
    if not product:
        raise NotFoundException("Product not found.")
    return forecast_repo.list_for_product(user.id, str(product_id))


@router.get("", response_model=List[ForecastRecord])
def list_all_forecasts(
    user: CurrentUser = Depends(get_current_user),
    forecast_repo: ForecastRepository = Depends(get_forecast_repository),
):
    return forecast_repo.list_for_user(user.id, order_by="forecast_date")
