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
from app.database.repositories.alerts import AlertRepository
from app.database.repositories.products import ProductRepository
from app.database.repositories.sales import SalesRepository
from app.schemas.inventory import DashboardSummary
from app.services.forecast_service import InsufficientDataError, generate_product_forecast
from app.services.inventory_service import compute_overstock_analysis, compute_stockout_prediction
from app.services.recommendation_service import build_reorder_recommendation, rank_recommendations

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    user: CurrentUser = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repository),
    sales_repo: SalesRepository = Depends(get_sales_repository),
    alert_repo: AlertRepository = Depends(get_alert_repository),
):
    products = product_repo.list_for_user(user.id)

    total_products = len(products)
    inventory_units = sum(int(p.get("current_stock") or 0) for p in products)
    inventory_value = sum(
        float(p.get("current_stock") or 0) * float(p.get("price") or 0) for p in products
    )

    low_stock_count = 0
    stockout_risk_count = 0
    overstock_count = 0
    capital_locked_total = 0.0
    expected_7_day_demand = 0.0
    recommendations = []

    for product in products:
        sales_rows = sales_repo.list_for_product(user.id, product["id"])

        stockout = compute_stockout_prediction(product, sales_rows)
        if stockout["stockout_risk"] in ("CRITICAL", "HIGH"):
            stockout_risk_count += 1
        elif float(product.get("current_stock") or 0) <= stockout["reorder_point"]:
            low_stock_count += 1

        overstock = compute_overstock_analysis(product, sales_rows)
        if overstock["overstock"]:
            overstock_count += 1
            capital_locked_total += overstock["capital_locked"]

        try:
            forecast = generate_product_forecast(sales_rows, horizon_days=7)
            expected_7_day_demand += forecast.total_demand()
        except InsufficientDataError:
            pass

        try:
            recommendations.append(build_reorder_recommendation(product, sales_rows))
        except Exception:
            continue

    ranked = rank_recommendations(recommendations)
    top_recommendations = [
        r for r in ranked if r["risk"] in ("CRITICAL", "HIGH", "MEDIUM") or r["recommended_order_quantity"] > 0
    ][:5]

    recent_alerts = alert_repo.list_active(user.id, limit=5)

    return {
        "total_products": total_products,
        "inventory_units": inventory_units,
        "inventory_value": round(inventory_value, 2),
        "low_stock_products": low_stock_count,
        "stockout_risk_products": stockout_risk_count,
        "overstock_products": overstock_count,
        "capital_locked": round(capital_locked_total, 2),
        "expected_7_day_demand": round(expected_7_day_demand, 2),
        "top_reorder_recommendations": top_recommendations,
        "recent_alerts": recent_alerts,
    }
