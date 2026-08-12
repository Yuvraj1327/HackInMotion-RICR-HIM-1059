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
from app.schemas.inventory import ScenarioSimulateRequest, ScenarioSimulateResponse
from app.services.scenario_service import simulate_scenario

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.post("/simulate", response_model=ScenarioSimulateResponse)
def simulate(
    payload: ScenarioSimulateRequest,
    user: CurrentUser = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repository),
    sales_repo: SalesRepository = Depends(get_sales_repository),
):
    product = product_repo.get_by_id(user.id, str(payload.product_id))
    if not product:
        raise NotFoundException("Product not found.")

    sales_rows = sales_repo.list_for_product(user.id, str(payload.product_id))
    result = simulate_scenario(
        product, sales_rows, payload.demand_change_percent, payload.supplier_delay_days
    )
    return result
