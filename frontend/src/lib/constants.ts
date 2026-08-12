export const CATEGORIES = ["grocery", "fashion", "electronics", "cosmetics"] as const;
export type DemoCategory = (typeof CATEGORIES)[number];

export const CATEGORY_LABELS: Record<DemoCategory, string> = {
  grocery: "Grocery",
  fashion: "Fashion",
  electronics: "Electronics",
  cosmetics: "Cosmetics",
};

export const RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;
export type RiskLevel = (typeof RISK_LEVELS)[number];

export const ALERT_TYPES = [
  "STOCKOUT",
  "LOW_STOCK",
  "OVERSTOCK",
  "DEMAND_SPIKE",
  "DEMAND_DROP",
  "DATA_ANOMALY",
] as const;
export type AlertType = (typeof ALERT_TYPES)[number];

export const FORECAST_HORIZONS = [7, 14, 30] as const;
export type ForecastHorizon = (typeof FORECAST_HORIZONS)[number];

/**
 * "Continue as Guest" (Login.tsx / useAuth.tsx) creates a real, throwaway
 * Supabase-authenticated user via the existing /auth/register endpoint,
 * then seeds it with real backend demo data via /demo/seed. This flag is
 * a purely presentational marker (which key drives the DEMO MODE badge)
 * — it grants no extra access and bypasses no auth/RLS check; the guest
 * is an ordinary authenticated user like any other, scoped to their own
 * data exactly the same way.
 */
export const GUEST_MODE_STORAGE_KEY = "stockpilot_guest_mode";

/** Demo dataset seeded automatically when a guest session starts. */
export const GUEST_DEMO_SEED = {
  business_category: "grocery",
  days_of_history: 120,
  num_products: 20,
} as const;

export const QUERY_KEYS = {
  products: ["products"] as const,
  product: (id: string) => ["products", id] as const,
  suppliers: ["suppliers"] as const,
  sales: (productId?: string) => ["sales", productId ?? "all"] as const,
  forecasts: (productId?: string) => ["forecasts", productId ?? "all"] as const,
  stockout: (productId?: string) => ["inventory", "stockout", productId ?? "all"] as const,
  overstock: (productId?: string) => ["inventory", "overstock", productId ?? "all"] as const,
  alerts: ["alerts"] as const,
  recommendations: ["recommendations"] as const,
  dashboard: ["dashboard", "summary"] as const,
};