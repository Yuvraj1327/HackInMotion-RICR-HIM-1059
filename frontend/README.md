# StockPilot AI — Frontend

**Predict demand. Prevent stockouts. Protect cash.**

React + TypeScript frontend for StockPilot AI, an AI-powered inventory and
demand forecasting platform. This app is a pure client for the existing
FastAPI backend — all forecasting, inventory math, and business logic live
server-side; the frontend only displays data, collects input, and calls the
API.

---

## 1. Project Overview

Built for the RICR Bhopal Hackathon. Pages: Login/Signup, Dashboard,
Inventory (CRUD), Product Details, Sales Data (CSV upload + demo
generator), Forecasts, Alerts, Reorder Recommendations, Scenario
Simulator, and Settings (suppliers + danger-zone data reset).

## 2. Requirements

- Node.js 18+ and npm
- A running instance of the StockPilot AI FastAPI backend
- A Supabase project (the **same** project the backend is configured
  against — see the backend's `README.md` for setup)

## 3. Tech Stack

React 18, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query,
Axios, Recharts, Lucide icons, Supabase JS client. UI primitives are
hand-built (Tailwind + Radix-style patterns) rather than a full component
library, to keep the bundle lean.

## 4. Installation

```bash
cd frontend
npm install
cp .env.example .env   # then fill in the values below
npm run dev
```

Runs at `http://localhost:5173`.

## 5. Environment Variables

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | FastAPI base URL **including** the `/api/v1` prefix, e.g. `http://localhost:8000/api/v1` |
| `VITE_SUPABASE_URL` | Same Supabase project URL the backend uses |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon/public key (safe for browser use) |

Only variables prefixed `VITE_` are exposed to client code — this is a
Vite requirement, not a StockPilot-specific choice. Never put the
Supabase **service-role** key here; that key is backend-only.

Production example:
```
VITE_API_BASE_URL=https://your-production-api.com/api/v1
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

## 6. Supabase Configuration

This frontend must point at the **same Supabase project** as the backend
(same `SUPABASE_URL`/anon key pair), because the access token issued by
`supabase.auth.signInWithPassword` here is verified by the backend using
that project's JWT secret. Pointing the frontend and backend at different
Supabase projects will make every authenticated API call fail with 401.

## 7. Running

```bash
npm run dev       # start Vite dev server (localhost:5173)
npm run build     # type-check (tsc -b) + production build to dist/
npm run preview   # locally preview the production build
```

`npm run build` runs the full TypeScript project build before bundling —
a type error anywhere in `src/` will fail the build, which doubles as a
lightweight CI check.

## 8. Deployment

`npm run build` outputs static files to `dist/`. Deploy `dist/` to any
static host (Vercel, Netlify, Cloudflare Pages, S3+CloudFront, etc.) and
set the three `VITE_*` environment variables in that host's build
configuration — they're baked in at build time, not read at runtime, so
each environment (staging/production) needs its own build. Set the
backend's `FRONTEND_URL` to match the deployed frontend's origin so CORS
allows it.

## 9. Authentication Flow

```
React (Login/Signup form)
  → Supabase JS client (supabase.auth.signInWithPassword / signUp)
  → Supabase Auth issues a JWT access token + refresh token
  → Supabase JS client persists the session (localStorage) and
    auto-refreshes the access token in the background
  → Axios request interceptor (src/api/client.ts) reads the current
    session on every request and attaches:
        Authorization: Bearer <access_token>
  → FastAPI verifies the JWT signature/expiry against SUPABASE_JWT_SECRET
    and extracts the user id
  → Every database query the backend makes is scoped to that user id
```

**Signup** is a special case: it calls the backend's `POST /auth/register`
(not Supabase directly), because that endpoint creates both the Supabase
Auth user *and* the corresponding `profiles` row (with `business_name`) in
one transaction using the backend's service-role key. The returned
`access_token`/`refresh_token` are then handed to
`supabase.auth.setSession(...)` so the Supabase JS client's own session
store — and therefore its auto-refresh behavior — takes over from that
point on, identically to a client-side signup.

**Login** goes straight through the Supabase JS client
(`signInWithPassword`), since it needs no extra backend-side setup.

**401 handling**: the Axios response interceptor catches any `401`, tries
exactly one `supabase.auth.refreshSession()`, retries the original
request once with the refreshed token, and — only if the refresh itself
fails (session genuinely expired) — signs the user out and redirects to
`/login`. This satisfies "attempt to refresh the session where
appropriate; if authentication is genuinely expired, log out."

**Protected routes**: `ProtectedRoute` / `PublicOnlyRoute`
(`src/components/common/ProtectedRoute.tsx`) gate every application route
based on `useAuth().isAuthenticated`, redirecting unauthenticated users to
`/login` (preserving the originally-requested path for a post-login
redirect) and authenticated users away from `/login`/`/signup`.

## 10. API Integration Architecture

```
src/api/client.ts     — single shared Axios instance: reads VITE_API_BASE_URL,
                         attaches the bearer token, normalizes every error
                         into an ApiError with a user-safe message, and
                         handles the 401-refresh-and-retry flow.
src/api/*.ts           — one thin module per backend resource (products.ts,
                         sales.ts, forecasts.ts, ...), each just a set of
                         typed functions wrapping an apiClient call. No
                         business logic lives here.
src/types/api.ts       — TypeScript interfaces mirroring the FastAPI/Pydantic
                         schemas exactly (verified against the live
                         /openapi.json spec, not guessed).
src/hooks / pages       — TanStack Query for all server state (useQuery for
                         reads, useMutation for writes), invalidating the
                         relevant query keys after each mutation so the UI
                         reflects the backend's actual state rather than an
                         optimistic guess.
```

Every number shown in the UI — dashboard metrics, stockout risk, reorder
quantities, forecast values, scenario results — comes directly from a
backend response. The frontend never computes forecasting, stockout
prediction, reorder math, or risk classification itself; where a value
needs light formatting (currency abbreviation, date formatting,
aggregating raw sales rows into a daily total for the chart's historical
line) that is presentation-only and never re-derives a number the backend
already calculates and returns via its own field.

## 11. Backend Endpoints Actually Used

```
POST   /api/v1/auth/register
GET    /api/v1/auth/me                          (currently unused by pages, available if needed)
POST   /api/v1/products            GET /api/v1/products
GET    /api/v1/products/{id}       PUT /api/v1/products/{id}    DELETE /api/v1/products/{id}
POST   /api/v1/suppliers           GET /api/v1/suppliers
PUT    /api/v1/suppliers/{id}      DELETE /api/v1/suppliers/{id}
POST   /api/v1/sales               GET /api/v1/sales
POST   /api/v1/sales/upload
POST   /api/v1/demo/seed           POST /api/v1/demo/reset
POST   /api/v1/forecasts/generate/{product_id}
GET    /api/v1/forecasts/{product_id}
GET    /api/v1/inventory/stockout          GET /api/v1/inventory/stockout/{id}
GET    /api/v1/inventory/overstock
GET    /api/v1/alerts              POST /api/v1/alerts/{id}/resolve
GET    /api/v1/recommendations/reorder
POST   /api/v1/scenarios/simulate
GET    /api/v1/dashboard/summary
```
`GET /api/v1/auth/login` is implemented in `src/api/auth.ts` but unused by
the UI (login goes through Supabase directly per the auth flow above) —
kept available for parity with the backend's documented surface.

## 12. Local Development (frontend + backend together)

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload --port 8000

# terminal 2
cd frontend && npm run dev
```

Backend's `FRONTEND_URL` must be `http://localhost:5173` (the default in
its `.env.example`) for CORS to allow the dev server.

## 13. Known Limitations / Integration Notes

- **`days_of_inventory` backend addition:** the Product Details page needs
  to show "days of inventory" (current stock ÷ average daily demand).
  The backend's `StockoutPrediction` response did not originally expose
  this value, even though it already computed it internally. Rather than
  compute it in React (which would duplicate backend business logic), the
  backend's `StockoutPrediction` schema and `inventory_service.py` were
  updated to include a `days_of_inventory` field, and the frontend simply
  displays it. This is the one backend change this frontend build
  required.
- **CSV upload success semantics:** `POST /sales/upload` returns HTTP 200
  even when the import itself failed (e.g. missing required columns) —
  failure is signaled via `success: false` in the JSON body, not the HTTP
  status. `uploadSalesCsv` callers must check `result.success`, not just
  whether the request resolved; `CsvUploadCard` does this correctly.
- **No live Supabase project in this environment:** end-to-end
  verification here confirmed the JWT handshake (frontend token →
  backend verification → reaching authorized business logic), CORS
  configuration against the exact frontend origin, Pydantic validation
  running before any database access, and clean (non-leaking) error
  responses when the database call itself fails — but full product
  create → forecast → alert → recommendation flows against real rows
  could not be exercised without live Supabase credentials. Once
  `SUPABASE_URL`/`SUPABASE_ANON_KEY`/`SUPABASE_SERVICE_ROLE_KEY`/
  `SUPABASE_JWT_SECRET` point at a real project, the acceptance flow in
  the original spec (signup → demo seed → forecast → alerts →
  recommendations → scenario → CRUD → CSV upload → logout → route
  protection → per-user data isolation) is what to run manually before a
  live demo.
- Auth endpoints (`/auth/register`, `/auth/login`) are a backend
  convenience wrapper, not a Supabase requirement — see the backend
  README's equivalent note.
