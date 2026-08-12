from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SaleCreate(BaseModel):
    product_id: UUID
    sale_date: date
    quantity: int = Field(..., ge=0)
    unit_price: float = Field(..., ge=0)
    promotion: bool = False


class SaleResponse(BaseModel):
    id: UUID
    user_id: UUID
    product_id: UUID
    sale_date: date
    quantity: int
    unit_price: float
    promotion: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CSVImportWarning(BaseModel):
    row: int
    reason: str


class CSVImportResult(BaseModel):
    success: bool
    total_rows: int
    imported_rows: int
    duplicate_rows: int
    invalid_rows: int
    warnings: List[CSVImportWarning] = []
