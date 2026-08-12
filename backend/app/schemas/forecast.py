from datetime import date, datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ForecastGenerateRequest(BaseModel):
    horizon_days: Literal[7, 14, 30] = 7


class ForecastPoint(BaseModel):
    date: date
    predicted_demand: float
    lower_bound: float
    upper_bound: float


class ForecastMetrics(BaseModel):
    mae: Optional[float] = None
    rmse: Optional[float] = None
    mape: Optional[float] = None


class ForecastGenerateResponse(BaseModel):
    product_id: UUID
    product_name: str
    model: str
    forecast: List[ForecastPoint]
    confidence: float
    metrics: ForecastMetrics
    training_records: int
    notes: Optional[str] = None


class ForecastRecord(BaseModel):
    id: UUID
    product_id: UUID
    forecast_date: date
    predicted_demand: float
    lower_bound: float
    upper_bound: float
    model_name: str
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}
