from typing import Literal

from pydantic import BaseModel, Field


class DemoSeedRequest(BaseModel):
    business_category: Literal["grocery", "fashion", "electronics", "cosmetics"] = "grocery"
    days_of_history: int = Field(default=120, ge=90, le=180)
    num_products: int = Field(default=20, ge=15, le=25)


class DemoSeedResponse(BaseModel):
    success: bool
    business_category: str
    products_created: int
    suppliers_created: int
    sales_records_created: int
    date_range_start: str
    date_range_end: str
