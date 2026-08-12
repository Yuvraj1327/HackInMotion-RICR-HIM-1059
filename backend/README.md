# StockPilot AI — Backend

AI-powered inventory and demand forecasting backend for retailers and
e-commerce businesses. Built for the **RICR Bhopal Hackathon**.

> This repository contains **only the backend**. The React frontend is a
> separate project that will consume this API.

---

## 1. Project Overview

StockPilot AI answers seven questions for a retail business:

1. What products are likely to run out of stock?
2. When will they run out?
3. Which products are overstocked?
4. What will demand look like over the next 7/30 days?
5. How many units should be reordered?
6. When should they be reordered?
7. Why is the system making that recommendation?

**Flow:** Historical Sales → Data Processing → Demand Forecast → Inventory
Risk Analysis → Stockout/Overstock Detection → Reorder Recommendation →
Business Action.

Because real businesses may not have historical data ready for a live demo,
the backend supports **both** CSV upload of real sales data **and** a
realistic synthetic demo-data generator.

---

## 2. Architecture

```
backend/
├── app/
│   ├── main.py                     # FastAPI app, CORS, global error handlers
│   ├── api/v1/                     # Route handlers (thin - no business logic)
│   ├── core/                       # config, JWT security, dependencies, exceptions
│   ├── database/
│   │   ├── supabase.py             # Supabase client factory (anon + service role)
│   │   └── repositories/           # User-scoped Supabase query wrappers
│   ├── schemas/                    # Pydantic request/response models
│   ├── services/
│   │   ├── forecasting/            # Moving Average, Exp. Smoothing, XGBoost, selector
│   │   ├── sales_series.py         # Raw sales rows -> continuous daily series
│   │   ├── forecast_service.py     # Orchestrates forecasting for a product
│   │   ├── inventory_service.py    # Stockout / overstock / reorder math
│   │   ├── alert_service.py        # Smart alert generation
│   │   ├── recommendation_service.py
│   │   ├── scenario_service.py     # What-if simulator
│   │   ├── csv_service.py          # Defensive CSV import/validation
│   │   └── demo_data_service.py    # Realistic synthetic data generator
│   └── utils/                      # calculations.py (documented formulas), date/validation helpers
├── tests/                          # pytest suite (63 tests)
├── supabase_schema.sql             # Tables + Row Level Security policies
├── requirements.txt
├── .env.example
├── Dockerfile
├── api-documentation.md
└── README.md
```

**Design principle:** route handlers only parse requests, call a service,
and return a response — all business logic (forecasting, risk math, alert
rules) lives in `app/services/` and `app/utils/`, independently testable.

---

## 3. Tech Stack

- **API:** FastAPI + Python 3.11+, Pydantic v2
- **Database/Auth:** Supabase (PostgreSQL + Supabase Auth)
- **ML/Forecasting:** pandas, NumPy, statsmodels (Holt-Winters), scikit-learn, XGBoost
- **Testing:** pytest
- **Docs:** FastAPI's built-in Swagger (`/docs`) and ReDoc (`/redoc`)

---

## 4. Supabase Setup

1. Create a project at [supabase.com](https://supabase.com).
2. Go to **SQL Editor** → paste the contents of `supabase_schema.sql` → **Run**.
   This creates all tables (`profiles`, `products`, `suppliers`, `sales`,
   `forecasts`, `forecast_runs`, `alerts`, `events`) and enables **Row
   Level Security** with a `user_id = auth.uid()` policy on every
   user-owned table.
3. Go to **Project Settings → API** and copy:
   - Project URL → `SUPABASE_URL`
   - `anon` `public` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY` (**backend only, never
     ship this to the frontend**)
4. Go to **Project Settings → API → JWT Settings** and copy the **JWT
   Secret** → `SUPABASE_JWT_SECRET`.
5. (Optional, recommended for the hackathon demo) In **Authentication →
   Providers**, disable "Confirm email" so `register` → `login` works
   immediately without an inbox.

---

## 5. Environment Variables

Copy `.env.example` to `.env` and fill in the values from step 4 above:

```bash
cp .env.example .env
```

| Variable | Purpose |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Public key, safe for client use, used for Auth calls |
| `SUPABASE_SERVICE_ROLE_KEY` | Admin key, backend-only, bypasses RLS — the backend re-implements the same user_id filtering in every query as defense-in-depth |
| `SUPABASE_JWT_SECRET` | Used to locally verify Supabase-issued JWTs |
| `FRONTEND_URL` | Allowed CORS origin(s), comma-separated |

**Never commit `.env` or expose `SUPABASE_SERVICE_ROLE_KEY` to the frontend.**

---

## 6. Local Installation

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in real values
```

## 7. Running FastAPI

```bash
uvicorn app.main:app --reload --port 8000
```

Server runs at `http://localhost:8000`.

## 8. Swagger / API Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Full written documentation with example requests/responses: `api-documentation.md`

## 9. Demo Data Generation

```bash
curl -X POST localhost:8000/api/v1/demo/seed \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"business_category":"grocery","days_of_history":120,"num_products":20}'
```

Generates 15–25 realistic products (from a curated per-category catalog:
grocery, fashion, electronics, cosmetics), 3–5 suppliers, and 90–180 days
of daily sales history per product with:

- weekday/weekend demand variation (different multiplier per product —
  Milk behaves differently from a Bluetooth Speaker)
- a gentle random trend (±10–25% drift over the period)
- slow seasonality (a long sine-wave cycle)
- 1–3 promotional windows per product with a demand lift
- 1–2 random demand spikes and 1–2 random demand drops
- Gaussian noise scaled by a per-product volatility factor
- deliberately varied stock postures (some products seeded understocked,
  some overstocked, most balanced) so the demo showcases real stockout
  **and** overstock alerts, not just "everything is fine"

## 10. CSV Format

```csv
date,product_id,quantity,price,promotion
2026-07-01,P001,24,65,0
2026-07-02,P001,31,65,0
2026-07-03,P001,27,65,10
```
Upload via `POST /api/v1/sales/upload` (`multipart/form-data`, field `file`).
The importer validates columns, dates, quantities, and product ownership;
detects in-file and against-database duplicates; and **never crashes** on
malformed input — it reports per-row problems instead. See
`api-documentation.md` for the full response shape.

---

## 11. Forecasting Methodology

Three model families are implemented, from simple to sophisticated:

1. **Moving Average** (`app/services/forecasting/moving_average.py`) — mean
   of the last 7 days, held flat. Cheap, robust baseline, and the model of
   choice when there isn't enough data for anything richer.
2. **Exponential Smoothing** (`exponential_smoothing.py`, via
   `statsmodels.tsa.holtwinters.ExponentialSmoothing`) — adds trend when
   ≥10 days of history exist, and additive weekly seasonality
   (`seasonal_periods=7`) when ≥14 days exist, since retail demand very
   commonly has weekday/weekend structure.
3. **XGBoost** (`xgboost_model.py`) — gradient-boosted trees trained on
   lag features (`lag_1/7/14/30`), rolling means (`7/14/30`), and calendar
   features (day of week, day of month, month, weekend flag, promotion
   flag). Needs ≥45 days of history. Multi-step forecasts are produced
   **recursively**: each predicted day is appended to the history so the
   next day's lag features can be computed.

There is an absolute last-resort **`HistoricalAverageFallback`** for
products with fewer than 3 days of data (even fewer than Moving Average
needs), so the API never returns an error just because a product is brand
new — it returns a flat forecast and clearly labels it as a fallback.

### Why these three?

- Moving Average is the cheapest possible sane baseline and a safety net.
- Exponential Smoothing is a well-understood classical method that
  explicitly models trend and (weekly) seasonality — exactly the structure
  retail demand has — without needing much data.
- XGBoost captures non-linear interactions between lags, rolling stats,
  and calendar effects (e.g. "Fridays during a promotion") that the
  classical methods can't, but only once there's enough history to learn
  from (per rule #18 in the spec: prefer simple, reliable ML over
  unnecessarily complicated deep learning — no neural nets here).

## 12. Model Selection & Evaluation

For every `POST /forecasts/generate/{product_id}` call
(`app/services/forecasting/model_selector.py`):

1. Build a continuous daily demand series (zero-filled for no-sale days).
2. Hold out the last 5–14 days (scaled to ~20% of history, capped) as a
   validation set.
3. Fit every candidate model whose minimum-data requirement is met by the
   training portion.
4. Score each candidate's validation predictions with **MAE**, **RMSE**,
   and **MAPE**.
5. Select the candidate with the lowest validation **MAPE** (ties broken
   by RMSE).
6. **Refit** the winning model type on the *full* series and use it to
   generate the actual forecast returned to the caller.
7. Persist the selected model name, metrics, and training record count in
   `forecast_runs` for auditability. The forecast points themselves are
   stored in `forecasts`.

If a product has too little data for validation-based selection at all,
the pipeline falls back to Moving Average (or Historical Average for
near-empty history) and says so explicitly in the response's `notes`
field — the API never claims accuracy metrics it didn't actually compute.

## 13. Inventory Formulas

All formulas live in `app/utils/calculations.py`, fully documented inline.
Summary:

| Metric | Formula |
|---|---|
| Average Daily Demand | mean of last 14 days of (zero-filled) daily sales |
| Days of Inventory | `current_stock / average_daily_demand` (undefined/∞ when demand is 0) |
| Lead-Time Demand | `average_daily_demand × lead_time_days` |
| Safety Stock | `Z × demand_std_dev × sqrt(lead_time_days)`, Z=1.65 (~95% service level), unless the user configured a manual `safety_stock` override on the product |
| Reorder Point | `lead_time_demand + safety_stock` |
| Recommended Order Qty | `max(0, forecast_demand + safety_stock - current_stock)` |
| Overstock | flagged when `current_stock > 1.5 × forecast_30_day_demand`; `capital_locked = excess_units × cost_price` (cost price, not selling price) |

## 14. How Stockout Risk Is Calculated

1. Generate a 30-day forecast for the product.
2. Walk forward day-by-day, subtracting each day's predicted demand from
   current stock, until it reaches zero (or the horizon runs out) —
   `app.utils.calculations.estimate_stockout_date`.
3. Classify risk **relative to the supplier's lead time** (not an
   arbitrary fixed day count):
   - **CRITICAL** — stock runs out at or before the lead time (a reorder
     placed today would arrive too late).
   - **HIGH** — runs out within 2× lead time.
   - **MEDIUM** — runs out within 4× lead time.
   - **LOW** — runway exceeds 4× lead time, or no stockout predicted
     within the forecast horizon.

## 15. How Reorder Quantity Is Calculated

`recommended_order_quantity = max(0, forecast_demand_over_horizon + safety_stock - current_stock)`

using a 14-day forecast horizon for the reorder engine and 7-day for the
"forecast_7_days" figure shown alongside it in recommendations. Never
negative — if current stock already covers the forecast plus the safety
buffer, no reorder is suggested.

---

## 16. Security / Row Level Security

- **Auth:** Supabase Auth issues a JWT on login/register. Every protected
  FastAPI endpoint depends on `get_current_user`
  (`app/core/dependencies.py`), which verifies the JWT's signature and
  expiry locally (`app/core/security.py`) using `SUPABASE_JWT_SECRET`
  and extracts the user id from the `sub` claim.
- **Backend-level isolation:** the backend uses the Supabase
  **service-role** key (bypasses RLS) so it can perform its own
  JWT-verified authorization — but **every single repository query**
  (`app/database/repositories/*.py`) explicitly filters by `user_id`
  regardless, as defense-in-depth.
- **Database-level isolation:** `supabase_schema.sql` enables **Row Level
  Security** on every user-owned table with a policy of
  `auth.uid() = user_id`. This is a second, independent enforcement layer
  — even if a future code path queried Supabase directly with a user's own
  session (anon key + their JWT) instead of through this backend, RLS
  alone would still prevent cross-user data access.
- Data isolation is never left to the frontend alone.

---

## 17. Testing

```bash
cd backend
PYTHONPATH=. pytest tests/ -v
```

63 tests covering: JWT auth (valid/expired/tampered/wrong-audience
tokens), product validation and ownership isolation, CSV
validation/import (valid rows, missing columns, duplicates, invalid
rows, malformed files), demo data generation (product/supplier counts,
date coverage, weekly demand structure, per-product variation,
promotional periods), the forecasting engine (weekly-pattern series,
insufficient-data fallback, zero/constant demand, extreme outliers, all
three horizons), inventory math (days-of-inventory, reorder point, order
quantity, risk classification, overstock detection end-to-end), alert
generation (stockout/overstock/demand-spike detection, never crashes on
empty history), scenario simulation, and API-level integration tests
(auth guard, request validation, docs availability).

---

## 18. Deployment

The `Dockerfile` builds a production image:

```bash
docker build -t stockpilot-backend .
docker run -p 8000:8000 --env-file .env stockpilot-backend
```

Deploy the container to any platform that runs Docker images (Render,
Railway, Fly.io, AWS App Runner, etc.), point `FRONTEND_URL` at your
deployed React app's origin, and keep `SUPABASE_SERVICE_ROLE_KEY` as a
secret environment variable (never baked into the image or committed).

---

## 19. Known Limitations

- The `/api/v1/auth/*` endpoints are a convenience wrapper for
  demoing the backend standalone; in production the React frontend should
  use the Supabase JS client directly for auth (better refresh-token and
  session handling than proxying through this backend).
- XGBoost's recursive multi-step forecasting can compound error over long
  horizons (30 days) since each step's prediction feeds the next step's
  lag features — this is a known characteristic of recursive forecasting,
  mitigated by the model-selection step preferring whichever model
  actually validates best per product.
- Confidence intervals are a symmetric Gaussian approximation
  (`point ± z·residual_std`) rather than a full predictive distribution —
  a reasonable, standard approximation for a hackathon timeline, not a
  guarantee of exact coverage.
- The `events`/festival-uplift table exists in the schema for future use
  but no automatic uplift is applied yet (per the spec: "do not blindly
  apply fake multipliers" — real event effects should be learned from
  data as it accumulates, or configured explicitly).
- Alert de-duplication is "one open alert per (product, type)" — it
  doesn't yet suppress alerts that were resolved and then immediately
  re-triggered within the same day.
- No rate limiting / pagination cursor beyond simple `limit`/`offset` —
  fine for a hackathon-scale product catalog, would need revisiting for
  a catalog of thousands of SKUs.
