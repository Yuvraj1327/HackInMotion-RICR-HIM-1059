from datetime import date, datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class StockoutPrediction(BaseModel):
    product_id: UUID
    product_name: str
    current_stock: int
    average_daily_demand: float
    days_of_inventory: Optional[float] = None
    stockout_risk: RiskLevel
    estimated_stockout_date: Optional[date] = None
    days_until_stockout: Optional[int] = None
    reorder_point: float
    lead_time_demand: float
    safety_stock: float


class OverstockAnalysis(BaseModel):
    product_id: UUID
    product_name: str
    current_stock: int
    forecast_30_day_demand: float
    overstock: bool
    excess_units: float
    capital_locked: float
    recommendation: str


class AlertResponse(BaseModel):
    id: UUID
    product_id: Optional[UUID]
    alert_type: str
    severity: str
    title: str
    message: str
    recommended_action: Optional[str] = None
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReorderRecommendation(BaseModel):
    product_id: UUID
    product_name: str
    risk: RiskLevel
    current_stock: int
    forecast_7_days: float
    days_until_stockout: Optional[int]
    recommended_order_quantity: int
    reason: str


class ScenarioSimulateRequest(BaseModel):
    product_id: UUID
    demand_change_percent: float = 0.0
    supplier_delay_days: int = 0


class ScenarioSimulateResponse(BaseModel):
    product_id: UUID
    product_name: str
    baseline_demand_7d: float
    scenario_demand_7d: float
    baseline_risk: RiskLevel
    scenario_risk: RiskLevel
    baseline_stockout_date: Optional[date]
    scenario_stockout_date: Optional[date]
    baseline_days_until_stockout: Optional[int]
    scenario_days_until_stockout: Optional[int]
    additional_units_required: int
    baseline_recommended_order_quantity: int
    scenario_recommended_order_quantity: int


class DashboardSummary(BaseModel):
    total_products: int
    inventory_units: int
    inventory_value: float
    low_stock_products: int
    stockout_risk_products: int
    overstock_products: int
    capital_locked: float
    expected_7_day_demand: float
    top_reorder_recommendations: List[ReorderRecommendation]
    recent_alerts: List[AlertResponse]
