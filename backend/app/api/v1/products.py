from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentUser, get_current_user
from app.core.exceptions import NotFoundException
from app.database.repositories.products import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["Products"])


def get_repo() -> ProductRepository:
    return ProductRepository()


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(
    payload: ProductCreate,
    user: CurrentUser = Depends(get_current_user),
    repo: ProductRepository = Depends(get_repo),
):
    data = payload.model_dump(mode="json")
    data["user_id"] = user.id
    created = repo.create(data)
    return created


@router.get("", response_model=List[ProductResponse])
def list_products(
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    category: Optional[str] = Query(None),
    low_stock: bool = Query(False, description="Only products at/below safety stock"),
    overstock: bool = Query(False, description="Only products with very high stock (heuristic)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    repo: ProductRepository = Depends(get_repo),
):
    filters = {"category": category} if category else None
    products = repo.list_for_user(user.id, filters=filters, order_by="created_at", desc=True)

    if search:
        s = search.lower()
        products = [p for p in products if s in p["name"].lower() or s in p["sku"].lower()]

    if low_stock:
        products = [p for p in products if p["current_stock"] <= (p.get("safety_stock") or 0)]

    if overstock:
        # Lightweight heuristic filter (full overstock analysis lives in
        # /inventory/overstock and factors in forecast demand).
        products = [p for p in products if p["current_stock"] > 10 * max(p.get("safety_stock") or 1, 1)]

    return products[offset : offset + limit]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    repo: ProductRepository = Depends(get_repo),
):
    product = repo.get_by_id(user.id, str(product_id))
    if not product:
        raise NotFoundException("Product not found.")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    user: CurrentUser = Depends(get_current_user),
    repo: ProductRepository = Depends(get_repo),
):
    existing = repo.get_by_id(user.id, str(product_id))
    if not existing:
        raise NotFoundException("Product not found.")

    updates = payload.model_dump(mode="json", exclude_unset=True)
    if not updates:
        return existing

    updated = repo.update(user.id, str(product_id), updates)
    return updated


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    repo: ProductRepository = Depends(get_repo),
):
    existing = repo.get_by_id(user.id, str(product_id))
    if not existing:
        raise NotFoundException("Product not found.")
    repo.delete(user.id, str(product_id))
    return None
