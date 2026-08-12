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
from app.database.repositories.products import ProductRepository
from app.database.repositories.sales import SalesRepository
from app.database.repositories.suppliers import SupplierRepository
from app.database.supabase import get_service_client
from app.schemas.common import MessageResponse
from app.schemas.demo import DemoSeedRequest, DemoSeedResponse
from app.services.demo_data_service import generate_demo_dataset

router = APIRouter(prefix="/demo", tags=["Demo Data"])


@router.post("/seed", response_model=DemoSeedResponse)
def seed_demo_data(
    payload: DemoSeedRequest,
    user: CurrentUser = Depends(get_current_user),
    supplier_repo: SupplierRepository = Depends(get_supplier_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
    sales_repo: SalesRepository = Depends(get_sales_repository),
):
    dataset = generate_demo_dataset(
        user_id=user.id,
        business_category=payload.business_category,
        days_of_history=payload.days_of_history,
        num_products=payload.num_products,
    )

    # 1. Insert suppliers, capture generated ids
    created_suppliers = []
    for supplier in dataset["suppliers"]:
        created_suppliers.append(supplier_repo.create(supplier))

    # 2. Insert products, resolving supplier_id from the index placeholder
    created_products = []
    for product in dataset["products"]:
        supplier_index = product.pop("_supplier_index")
        product["supplier_id"] = created_suppliers[supplier_index]["id"]
        created_products.append(product_repo.create(product))

    # 3. Insert sales rows for each product in bulk chunks
    total_sales = 0
    for product_record, sales_rows in zip(created_products, dataset["sales_by_product"]):
        rows = [
            {**row, "user_id": user.id, "product_id": product_record["id"]}
            for row in sales_rows
        ]
        chunk_size = 500
        for i in range(0, len(rows), chunk_size):
            sales_repo.bulk_create(rows[i : i + chunk_size])
        total_sales += len(rows)

    return DemoSeedResponse(
        success=True,
        business_category=payload.business_category,
        products_created=len(created_products),
        suppliers_created=len(created_suppliers),
        sales_records_created=total_sales,
        date_range_start=dataset["date_range_start"],
        date_range_end=dataset["date_range_end"],
    )


@router.post("/reset", response_model=MessageResponse)
def reset_demo_data(user: CurrentUser = Depends(get_current_user)):
    """
    Deletes all products, suppliers, sales, forecasts, and alerts for the
    current user. Intended for resetting a hackathon demo between runs.
    Sales/forecasts/alerts cascade-delete via FK ON DELETE CASCADE when a
    product is removed (see supabase_schema.sql); suppliers are removed
    after products since products reference them.
    """
    client = get_service_client()
    client.table("products").delete().eq("user_id", user.id).execute()
    client.table("suppliers").delete().eq("user_id", user.id).execute()
    client.table("alerts").delete().eq("user_id", user.id).execute()
    client.table("sales").delete().eq("user_id", user.id).execute()
    client.table("forecasts").delete().eq("user_id", user.id).execute()
    client.table("forecast_runs").delete().eq("user_id", user.id).execute()
    return MessageResponse(message="Demo data reset successfully.")
