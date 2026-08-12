from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    sku: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    current_stock: int = Field(..., ge=0)
    price: float = Field(..., gt=0)
    cost_price: float = Field(..., gt=0)
    supplier_id: Optional[UUID] = None
    lead_time_days: int = Field(default=3, ge=0, le=365)
    safety_stock: int = Field(default=0, ge=0)
    unit: str = Field(default="unit", max_length=50)

    @field_validator("cost_price")
    @classmethod
    def cost_should_not_exceed_price_absurdly(cls, v, info):
        # Not a hard business rule, just a sanity guard against typos.
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    current_stock: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)
    cost_price: Optional[float] = Field(None, gt=0)
    supplier_id: Optional[UUID] = None
    lead_time_days: Optional[int] = Field(None, ge=0, le=365)
    safety_stock: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=50)


class ProductResponse(ProductBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
