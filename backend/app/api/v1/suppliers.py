from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, get_current_user
from app.core.exceptions import NotFoundException
from app.database.repositories.suppliers import SupplierRepository
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


def get_repo() -> SupplierRepository:
    return SupplierRepository()


@router.post("", response_model=SupplierResponse, status_code=201)
def create_supplier(
    payload: SupplierCreate,
    user: CurrentUser = Depends(get_current_user),
    repo: SupplierRepository = Depends(get_repo),
):
    data = payload.model_dump(mode="json")
    data["user_id"] = user.id
    return repo.create(data)


@router.get("", response_model=List[SupplierResponse])
def list_suppliers(
    user: CurrentUser = Depends(get_current_user),
    repo: SupplierRepository = Depends(get_repo),
):
    return repo.list_for_user(user.id, order_by="created_at", desc=True)


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    repo: SupplierRepository = Depends(get_repo),
):
    supplier = repo.get_by_id(user.id, str(supplier_id))
    if not supplier:
        raise NotFoundException("Supplier not found.")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: UUID,
    payload: SupplierUpdate,
    user: CurrentUser = Depends(get_current_user),
    repo: SupplierRepository = Depends(get_repo),
):
    existing = repo.get_by_id(user.id, str(supplier_id))
    if not existing:
        raise NotFoundException("Supplier not found.")
    updates = payload.model_dump(mode="json", exclude_unset=True)
    if not updates:
        return existing
    return repo.update(user.id, str(supplier_id), updates)


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(
    supplier_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    repo: SupplierRepository = Depends(get_repo),
):
    existing = repo.get_by_id(user.id, str(supplier_id))
    if not existing:
        raise NotFoundException("Supplier not found.")
    repo.delete(user.id, str(supplier_id))
    return None
