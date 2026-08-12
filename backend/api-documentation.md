# StockPilot AI — API Documentation

Base URL (local dev): `http://localhost:8000`
All business endpoints are prefixed with `/api/v1`.
Interactive docs: `/docs` (Swagger UI) and `/redoc`.

---

## Authentication

StockPilot AI uses **Supabase Auth**. The React frontend should authenticate
directly against Supabase (recommended), then send the resulting **access
token** on every request to this backend:

```
Authorization: Bearer <supabase_access_token>
```

The backend verifies the JWT's signature and expiry locally using
`SUPABASE_JWT_SECRET`, extracts the user id (`sub` claim), and scopes every
database query to that user.

For convenience/demo purposes, the backend also exposes thin wrapper
endpoints:

### `POST /api/v1/auth/register`
```json
{
  "email": "owner@retailstore.com",
  "password": "StrongPass123!",
  "business_name": "Sharma General Store"
}
```
**Response 201**
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "v1.Mzk...",
  "user_id": "b3f1c9a0-...",
  "email": "owner@retailstore.com"
}
```

### `POST /api/v1/auth/login`
```json
{ "email": "owner@retailstore.com", "password": "StrongPass123!" }
```
Response shape identical to register.

### `GET /api/v1/auth/me` *(protected)*
Returns `{ "user_id": "...", "email": "..." }` for the caller's token.

---

## Error Response Format

All errors return clean JSON, never a Python stack trace:

```json
{ "success": false, "error": "not_found", "detail": "Product not found." }
```

| HTTP Status | `error` value          | Meaning                                    |
|-------------|-------------------------|---------------------------------------------|
| 401         | `http_error`             | Missing/invalid/expired auth token          |
| 403         | `forbidden`               | Authenticated but not allowed               |
| 404         | `not_found`               | Resource doesn't exist / not owned by you   |
| 422         | `validation_error`        | Request body/query failed validation        |
| 422         | `insufficient_data`       | Not enough sales history for this operation |
| 500         | `internal_server_error`   | Unexpected error (details are logged server-side, never exposed) |

---

## Products — `/api/v1/products`

| Method | Path                     | Description                          |
|--------|--------------------------|---------------------------------------|
| POST   | `/products`               | Create a product                     |
| GET    | `/products`                | List products (search/filter)        |
| GET    | `/products/{id}`           | Get one product                      |
| PUT    | `/products/{id}`           | Update a product                     |
| DELETE | `/products/{id}`           | Delete a product                     |

**Create — request**
```json
{
  "name": "Milk 1L",
  "sku": "MILK001",
  "category": "Dairy",
  "current_stock": 42,
  "price": 65,
  "cost_price": 50,
  "lead_time_days": 2,
  "safety_stock": 20
}
```
**Response 201**
```json
{
  "id": "9c3e...",
  "user_id": "b3f1...",
  "name": "Milk 1L",
  "sku": "MILK001",
  "category": "Dairy",
  "current_stock": 42,
  "price": 65,
  "cost_price": 50,
  "supplier_id": null,
  "lead_time_days": 2,
  "safety_stock": 20,
  "unit": "unit",
  "created_at": "2026-08-12T10:00:00Z",
  "updated_at": "2026-08-12T10:00:00Z"
}
```

**List — query params**: `search`, `category`, `low_stock` (bool),
`overstock` (bool), `limit`, `offset`.

Validation: `current_stock >= 0`, `price > 0`, `cost_price > 0`,
`0 <= lead_time_days <= 365`, `safety_stock >= 0`.

---

## Suppliers — `/api/v1/suppliers`

Same CRUD shape as products.

```json
{
  "name": "Metro Distributors",
  "contact_name": "Rahul Sharma",
  "email": "contact@metro.com",
  "phone": "+91-9876543210",
  "lead_time_days": 4,
  "reliability_score": 0.95
}
```

---

## Sales — `/api/v1/sales`

| Method | Path            | Description                     |
|--------|-----------------|-----------------------------------|
| POST   | `/sales`         | Record a single sale             |
| GET    | `/sales`          | List sales (filter by product_id)|
| POST   | `/sales/upload`    | Bulk-import sales from a CSV file|

**CSV format** (`multipart/form-data`, field name `file`):
```csv
date,product_id,quantity,price,promotion
2026-07-01,P001,24,65,0
2026-07-02,P001,31,65,0
2026-07-03,P001,27,65,10
```
- `date`: any format `pandas.to_datetime` can parse (ISO recommended)
- `product_id`: must belong to the authenticated user
- `quantity`: integer >= 0
- `price`: numeric >= 0 (optional, defaults to 0)
- `promotion`: `1`/`0`, `true`/`false` (optional, defaults to `0`)

**Response**
```json
{
  "success": true,
  "total_rows": 1000,
  "imported_rows": 982,
  "duplicate_rows": 8,
  "invalid_rows": 10,
  "warnings": [
    { "row": 45, "reason": "quantity cannot be negative" }
  ]
}
```
The importer never crashes on malformed input — bad rows are reported,
not fatal.

---

## Demo Data — `/api/v1/demo`

### `POST /demo/seed`
```json
{
  "business_category": "grocery",
  "days_of_history": 120,
  "num_products": 20
}
```
`business_category` ∈ `grocery | fashion | electronics | cosmetics`.
`days_of_history` ∈ [90, 180]. `num_products` ∈ [15, 25].

**Response**
```json
{
  "success": true,
  "business_category": "grocery",
  "products_created": 20,
  "suppliers_created": 5,
  "sales_records_created": 2400,
  "date_range_start": "2026-04-14",
  "date_range_end": "2026-08-11"
}
```

### `POST /demo/reset`
Deletes all of the current user's products, suppliers, sales, forecasts,
and alerts. Returns `{ "success": true, "message": "Demo data reset successfully." }`.

---

## Forecasts — `/api/v1/forecasts`

### `POST /forecasts/generate/{product_id}`
```json
{ "horizon_days": 7 }
```
`horizon_days` ∈ `{7, 14, 30}`.

**Response**
```json
{
  "product_id": "9c3e...",
  "product_name": "Milk 1L",
  "model": "ExponentialSmoothing",
  "forecast": [
    { "date": "2026-08-13", "predicted_demand": 25.4, "lower_bound": 21.1, "upper_bound": 29.7 }
  ],
  "confidence": 0.89,
  "metrics": { "mae": 3.2, "rmse": 4.7, "mape": 8.4 },
  "training_records": 120,
  "notes": "Selected via validation on last 14 day(s); compared 3 candidate model(s)."
}
```
Generating a forecast persists it (`forecasts` table) and logs a
`forecast_runs` audit row with the evaluation metrics.

### `GET /forecasts/{product_id}` — most recently stored forecast points.
### `GET /forecasts` — all stored forecast points for the user.

If a product has no sales history at all, this returns
`422 insufficient_data`.

---

## Inventory Risk — `/api/v1/inventory`

### `GET /inventory/stockout/{product_id}` and `GET /inventory/stockout`
```json
{
  "product_id": "9c3e...",
  "product_name": "Milk 1L",
  "current_stock": 42,
  "average_daily_demand": 27.1,
  "days_of_inventory": 1.5,
  "stockout_risk": "HIGH",
  "estimated_stockout_date": "2026-08-15",
  "days_until_stockout": 2,
  "reorder_point": 78.3,
  "lead_time_demand": 54.2,
  "safety_stock": 24.1
}
```

### `GET /inventory/overstock/{product_id}` and `GET /inventory/overstock`
```json
{
  "product_id": "9c3e...",
  "product_name": "Bluetooth Speaker",
  "current_stock": 500,
  "forecast_30_day_demand": 120,
  "overstock": true,
  "excess_units": 380,
  "capital_locked": 34200,
  "recommendation": "Consider promotional pricing, bundling, or clearance..."
}
```

---

## Alerts — `/api/v1/alerts`

### `GET /alerts?resolved=false&limit=100`
Recomputes alerts from live data (stockout, overstock, demand spike/drop,
data anomaly) for every product, persists any newly-detected condition
(without duplicating an already-open alert of the same type), and
returns the current list.

```json
[
  {
    "id": "a1b2...",
    "product_id": "9c3e...",
    "alert_type": "STOCKOUT",
    "severity": "HIGH",
    "title": "Milk 1L at risk of stockout",
    "message": "Milk 1L is predicted to run out in 2 day(s).",
    "recommended_action": "Place a reorder now...",
    "resolved": false,
    "created_at": "2026-08-12T09:00:00Z"
  }
]
```

### `POST /alerts/{id}/resolve`
Marks an alert resolved and returns the updated alert.

---

## Reorder Recommendations — `/api/v1/recommendations/reorder`

```json
[
  {
    "product_id": "9c3e...",
    "product_name": "Milk 1L",
    "risk": "HIGH",
    "current_stock": 42,
    "forecast_7_days": 86,
    "days_until_stockout": 2,
    "recommended_order_quantity": 65,
    "reason": "Recommended because current inventory is below the reorder point and projected 7-day demand exceeds current stock."
  }
]
```
Sorted by severity (CRITICAL → HIGH → MEDIUM → LOW), then soonest
stockout, then largest recommended order quantity.

---

## What-If Scenario Simulator — `/api/v1/scenarios/simulate`

```json
{
  "product_id": "9c3e...",
  "demand_change_percent": 20,
  "supplier_delay_days": 3
}
```
**Response**
```json
{
  "product_id": "9c3e...",
  "product_name": "Milk 1L",
  "baseline_demand_7d": 150,
  "scenario_demand_7d": 180,
  "baseline_risk": "MEDIUM",
  "scenario_risk": "HIGH",
  "baseline_stockout_date": "2026-08-20",
  "scenario_stockout_date": "2026-08-17",
  "baseline_days_until_stockout": 8,
  "scenario_days_until_stockout": 5,
  "additional_units_required": 40,
  "baseline_recommended_order_quantity": 110,
  "scenario_recommended_order_quantity": 150
}
```

---

## Dashboard — `/api/v1/dashboard/summary`

```json
{
  "total_products": 20,
  "inventory_units": 4280,
  "inventory_value": 1280000,
  "low_stock_products": 4,
  "stockout_risk_products": 4,
  "overstock_products": 3,
  "capital_locked": 82000,
  "expected_7_day_demand": 4280,
  "top_reorder_recommendations": [ /* ReorderRecommendation[] */ ],
  "recent_alerts": [ /* AlertResponse[] */ ]
}
```

---

## Complete Demo Flow

```bash
# 1. Register
curl -X POST localhost:8000/api/v1/auth/register -H "Content-Type: application/json" \
  -d '{"email":"demo@shop.com","password":"Passw0rd!","business_name":"Demo Store"}'

# copy access_token from response into $TOKEN

# 2. Seed demo data
curl -X POST localhost:8000/api/v1/demo/seed -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"business_category":"grocery","days_of_history":120,"num_products":20}'

# 3. List products
curl localhost:8000/api/v1/products -H "Authorization: Bearer $TOKEN"

# 4. Generate a forecast for a product
curl -X POST localhost:8000/api/v1/forecasts/generate/<product_id> \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"horizon_days":7}'

# 5. Check stockout risk
curl localhost:8000/api/v1/inventory/stockout/<product_id> -H "Authorization: Bearer $TOKEN"

# 6. Get reorder recommendations
curl localhost:8000/api/v1/recommendations/reorder -H "Authorization: Bearer $TOKEN"

# 7. Run a what-if scenario
curl -X POST localhost:8000/api/v1/scenarios/simulate -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id":"<product_id>","demand_change_percent":20,"supplier_delay_days":3}'

# 8. Dashboard summary
curl localhost:8000/api/v1/dashboard/summary -H "Authorization: Bearer $TOKEN"
```
