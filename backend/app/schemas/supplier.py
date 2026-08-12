from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    contact_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    lead_time_days: int = Field(default=3, ge=0, le=365)
    reliability_score: float = Field(default=0.9, ge=0, le=1)


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    contact_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    lead_time_days: Optional[int] = Field(None, ge=0, le=365)
    reliability_score: Optional[float] = Field(None, ge=0, le=1)


class SupplierResponse(SupplierBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
