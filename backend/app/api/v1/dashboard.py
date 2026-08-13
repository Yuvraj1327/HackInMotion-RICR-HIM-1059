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
from app.services.sales_series import group_sales_by_product

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

    # Fetch every one of this user's sales rows in a SINGLE request and
    # group them by product in memory, instead of issuing one sales
    # query per product (an N+1 pattern that turns into N sequential
    # database round-trips for an N-product catalog). `list_for_user` is
    # the same generic repository method already used elsewhere in the
    # codebase (products, suppliers, alerts) - no new API added.
    all_sales = sales_repo.list_for_user(user.id)
    sales_by_product = group_sales_by_product(all_sales)

    low_stock_count = 0
    stockout_risk_count = 0
    overstock_count = 0
    capital_locked_total = 0.0
    expected_7_day_demand = 0.0
    recommendations = []

    for product in products:
        sales_rows = sales_by_product.get(product["id"], [])

        # Fit the demand model ONCE per product (at the longest horizon
        # any calculation below needs, 30 days) and reuse that single
        # result for stockout risk, overstock detection, the 7-day
        # expected-demand total, and the reorder recommendation - rather
        # than independently re-fitting the model up to six times per
        # product, which is what made this endpoint slow for accounts
        # with enough sales history to trigger the more expensive
        # candidate models. Model selection doesn't depend on the
        # requested horizon (only the final prediction step does), so
        # slicing a 30-day forecast's first 7/14 points is numerically
        # identical to generating a fresh 7/14-day forecast directly.
        try:
            forecast_30d = generate_product_forecast(sales_rows, horizon_days=30)
        except InsufficientDataError:
            forecast_30d = None

        stockout = compute_stockout_prediction(product, sales_rows, forecast_30d=forecast_30d)
        if stockout["stockout_risk"] in ("CRITICAL", "HIGH"):
            stockout_risk_count += 1
        elif float(product.get("current_stock") or 0) <= stockout["reorder_point"]:
            low_stock_count += 1

        overstock = compute_overstock_analysis(product, sales_rows, forecast_30d=forecast_30d)
        if overstock["overstock"]:
            overstock_count += 1
            capital_locked_total += overstock["capital_locked"]

        if forecast_30d is not None:
            expected_7_day_demand += forecast_30d.total_demand(7)

        try:
            recommendations.append(build_reorder_recommendation(product, sales_rows, forecast_30d=forecast_30d))
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