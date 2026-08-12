// These interfaces mirror the FastAPI/Pydantic schemas exactly (verified
// against the live OpenAPI spec at /openapi.json). Keep in sync if the
// backend schemas change.

export interface Product {
  id: string;
  user_id: string;
  name: string;
  sku: string;
  category: string;
  current_stock: number;
  price: number;
  cost_price: number;
  supplier_id: string | null;
  lead_time_days: number;
  safety_stock: number;
  unit: string;
  created_at: string;
  updated_at: string;
}

export interface ProductCreateInput {
  name: string;
  sku: string;
  category: string;
  current_stock: number;
  price: number;
  cost_price: number;
  supplier_id?: string | null;
  lead_time_days?: number;
  safety_stock?: number;
  unit?: string;
}

export type ProductUpdateInput = Partial<ProductCreateInput>;

export interface Supplier {
  id: string;
  user_id: string;
  name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  lead_time_days: number;
  reliability_score: number;
  created_at: string;
  updated_at: string;
}

export interface SupplierCreateInput {
  name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  lead_time_days?: number;
  reliability_score?: number;
}

export type SupplierUpdateInput = Partial<SupplierCreateInput>;

export interface Sale {
  id: string;
  user_id: string;
  product_id: string;
  sale_date: string;
  quantity: number;
  unit_price: number;
  promotion: boolean;
  created_at: string;
}

export interface SaleCreateInput {
  product_id: string;
  sale_date: string;
  quantity: number;
  unit_price: number;
  promotion?: boolean;
}

export interface CSVImportWarning {
  row: number;
  reason: string;
}

export interface CSVImportResult {
  success: boolean;
  total_rows: number;
  imported_rows: number;
  duplicate_rows: number;
  invalid_rows: number;
  warnings: CSVImportWarning[];
}

export interface ForecastPoint {
  date: string;
  predicted_demand: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ForecastMetrics {
  mae: number | null;
  rmse: number | null;
  mape: number | null;
}

export interface ForecastGenerateResponse {
  product_id: string;
  product_name: string;
  model: string;
  forecast: ForecastPoint[];
  confidence: number;
  metrics: ForecastMetrics;
  training_records: number;
  notes: string | null;
}

export interface ForecastRecord {
  id: string;
  product_id: string;
  forecast_date: string;
  predicted_demand: number;
  lower_bound: number;
  upper_bound: number;
  model_name: string;
  confidence: number;
  created_at: string;
}

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface StockoutPrediction {
  product_id: string;
  product_name: string;
  current_stock: number;
  average_daily_demand: number;
  days_of_inventory: number | null;
  stockout_risk: RiskLevel;
  estimated_stockout_date: string | null;
  days_until_stockout: number | null;
  reorder_point: number;
  lead_time_demand: number;
  safety_stock: number;
}

export interface OverstockAnalysis {
  product_id: string;
  product_name: string;
  current_stock: number;
  forecast_30_day_demand: number;
  overstock: boolean;
  excess_units: number;
  capital_locked: number;
  recommendation: string;
}

export type AlertType =
  | "STOCKOUT"
  | "LOW_STOCK"
  | "OVERSTOCK"
  | "DEMAND_SPIKE"
  | "DEMAND_DROP"
  | "DATA_ANOMALY";

export interface Alert {
  id: string;
  product_id: string | null;
  alert_type: AlertType;
  severity: RiskLevel;
  title: string;
  message: string;
  recommended_action: string | null;
  resolved: boolean;
  created_at: string;
}

export interface ReorderRecommendation {
  product_id: string;
  product_name: string;
  risk: RiskLevel;
  current_stock: number;
  forecast_7_days: number;
  days_until_stockout: number | null;
  recommended_order_quantity: number;
  reason: string;
}

export interface ScenarioSimulateInput {
  product_id: string;
  demand_change_percent: number;
  supplier_delay_days: number;
}

export interface ScenarioSimulateResponse {
  product_id: string;
  product_name: string;
  baseline_demand_7d: number;
  scenario_demand_7d: number;
  baseline_risk: RiskLevel;
  scenario_risk: RiskLevel;
  baseline_stockout_date: string | null;
  scenario_stockout_date: string | null;
  baseline_days_until_stockout: number | null;
  scenario_days_until_stockout: number | null;
  additional_units_required: number;
  baseline_recommended_order_quantity: number;
  scenario_recommended_order_quantity: number;
}

export interface DashboardSummary {
  total_products: number;
  inventory_units: number;
  inventory_value: number;
  low_stock_products: number;
  stockout_risk_products: number;
  overstock_products: number;
  capital_locked: number;
  expected_7_day_demand: number;
  top_reorder_recommendations: ReorderRecommendation[];
  recent_alerts: Alert[];
}

export type DemoCategoryInput = "grocery" | "fashion" | "electronics" | "cosmetics";

export interface DemoSeedInput {
  business_category: DemoCategoryInput;
  days_of_history: number;
  num_products: number;
}

export interface DemoSeedResponse {
  success: boolean;
  business_category: string;
  products_created: number;
  suppliers_created: number;
  sales_records_created: number;
  date_range_start: string;
  date_range_end: string;
}

export interface MessageResponse {
  success: boolean;
  message: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  business_name: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string | null;
  user_id: string;
  email: string;
}

/** Shape of every error response the FastAPI backend returns (see main.py global exception handlers). */
export interface ApiErrorBody {
  success: false;
  error: string;
  detail: string | Array<{ loc: (string | number)[]; msg: string; type: string }>;
}
