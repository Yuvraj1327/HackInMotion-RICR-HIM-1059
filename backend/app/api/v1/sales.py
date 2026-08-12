from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.dependencies import CurrentUser, get_current_user
from app.core.exceptions import NotFoundException, ValidationException
from app.database.repositories.products import ProductRepository
from app.database.repositories.sales import SalesRepository
from app.schemas.sales import CSVImportResult, SaleCreate, SaleResponse
from app.services.csv_service import parse_and_validate_csv

router = APIRouter(prefix="/sales", tags=["Sales"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def get_repo() -> SalesRepository:
    return SalesRepository()


def get_product_repo() -> ProductRepository:
    return ProductRepository()


@router.post("", response_model=SaleResponse, status_code=201)
def create_sale(
    payload: SaleCreate,
    user: CurrentUser = Depends(get_current_user),
    repo: SalesRepository = Depends(get_repo),
    product_repo: ProductRepository = Depends(get_product_repo),
):
    product = product_repo.get_by_id(user.id, str(payload.product_id))
    if not product:
        raise NotFoundException("Product not found.")

    data = payload.model_dump(mode="json")
    data["user_id"] = user.id
    return repo.create(data)


@router.get("", response_model=List[SaleResponse])
def list_sales(
    product_id: Optional[UUID] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    repo: SalesRepository = Depends(get_repo),
):
    filters = {"product_id": str(product_id)} if product_id else None
    return repo.list_for_user(
        user.id, filters=filters, order_by="sale_date", desc=True, limit=limit, offset=offset
    )


@router.post("/upload", response_model=CSVImportResult)
async def upload_sales_csv(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    repo: SalesRepository = Depends(get_repo),
    product_repo: ProductRepository = Depends(get_product_repo),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ValidationException("Please upload a .csv file.")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise ValidationException("CSV file is too large (max 10MB).")

    products = product_repo.list_for_user(user.id)
    valid_product_ids = {p["id"] for p in products}
    existing_keys = repo.existing_keys_for_user(user.id)

    valid_rows, stats = parse_and_validate_csv(contents, valid_product_ids, existing_keys)

    for row in valid_rows:
        row["user_id"] = user.id

    if valid_rows:
        # Insert in chunks to stay well under typical request-size limits.
        chunk_size = 500
        for i in range(0, len(valid_rows), chunk_size):
            repo.bulk_create(valid_rows[i : i + chunk_size])

    return stats
