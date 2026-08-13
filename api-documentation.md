# StockPilot AI --- API Documentation

## 1. Overview

StockPilot AI uses a REST API built with **FastAPI**.

### Base URL

Development:

``` text
http://127.0.0.1:8000/api/v1
```

Swagger/OpenAPI:

``` text
http://127.0.0.1:8000/docs
```

All protected endpoints require a valid Supabase access token:

``` http
Authorization: Bearer <access_token>
```

------------------------------------------------------------------------

## 2. Authentication

StockPilot uses **Supabase Auth** for authentication and FastAPI for
protected business APIs.

### Authentication Flow

``` text
React
  ↓
FastAPI Auth Endpoint
  ↓
Supabase Auth
  ↓
Access Token
  ↓
Authorization: Bearer <token>
  ↓
Protected FastAPI API
```

------------------------------------------------------------------------

# 3. Authentication APIs

## POST `/auth/register`

Create a new business user.

### Request

``` json
{
  "email": "owner@example.com",
  "password": "StrongPassword123",
  "business_name": "ABC Store"
}
```

### Success

``` text
200/201 Created
```

The exact response schema is defined by the current FastAPI
implementation.

### Possible Errors

  Status   Meaning
  -------- ------------------------------------
  400      Invalid registration data
  409      User already exists
  429      Supabase authentication rate limit
  500      Server error

------------------------------------------------------------------------

## POST `/auth/login`

Authenticate an existing business user.

### Request

``` json
{
  "email": "owner@example.com",
  "password": "StrongPassword123"
}
```

### Success

Returns an authentication response containing an access token/session
information.

The frontend must use the access token for protected requests:

``` http
Authorization: Bearer <access_token>
```

------------------------------------------------------------------------

## POST `/auth/guest`

Create or authenticate a demo/guest session.

This endpoint is used by **Continue as Guest**.

### Important

Guest Mode does **not** use the normal registration endpoint.

### Flow

``` text
Continue as Guest
        ↓
POST /auth/guest
        ↓
Demo user/session
        ↓
Access token
        ↓
Demo data
        ↓
Dashboard
```

### Success

``` text
201 Created
```

The response contains the authentication information required by the
frontend.

Guest data must remain isolated from real business users.

------------------------------------------------------------------------

# 4. Demo APIs

## POST `/demo/seed`

Seeds realistic demo inventory/sales data for the authenticated demo
user.

### Authentication

Required.

``` http
Authorization: Bearer <access_token>
```

### Purpose

Used after Guest login to populate the dashboard with realistic sample
data.

### Expected Flow

``` text
Guest Login
→ /demo/seed
→ Products + Sales + Inventory
→ Forecast/Alert calculations
→ Dashboard
```

### Errors

  Status   Meaning
  -------- ----------------------------
  401      Missing/invalid token
  400      Demo data cannot be seeded
  500      Server error

------------------------------------------------------------------------

## POST `/demo/reset`

Resets demo data for the current demo session.

### Authentication

Required.

``` http
Authorization: Bearer <access_token>
```

This endpoint should only affect the current demo user's data.

------------------------------------------------------------------------

# 5. Dashboard APIs

## GET `/dashboard/summary`

Returns the summary information used by the main dashboard.

### Authentication

Required.

### Example

``` http
GET /api/v1/dashboard/summary
Authorization: Bearer <access_token>
```

### Data

The dashboard summary can include information such as:

-   Total products
-   Inventory status/value
-   Stockout risks
-   Overstock risks
-   Sales information
-   Forecast information
-   Reorder recommendations

The exact response structure follows the current backend schema.

------------------------------------------------------------------------

# 6. Product APIs

## GET `/products`

Returns products belonging to the authenticated user.

### Query Parameters

Example:

``` text
/products?limit=500
```

### Authentication

Required.

### Example

``` http
GET /api/v1/products?limit=500
Authorization: Bearer <access_token>
```

------------------------------------------------------------------------

## POST `/products`

Creates a product.

Typical product information includes:

``` json
{
  "name": "Wireless Mouse",
  "category": "Electronics",
  "current_stock": 25,
  "price": 799,
  "supplier_id": "supplier-id"
}
```

The exact required fields must match the current FastAPI product schema.

------------------------------------------------------------------------

## PUT/PATCH `/products/{product_id}`

Updates an existing product.

Only the authenticated user's product should be modified.

------------------------------------------------------------------------

## DELETE `/products/{product_id}`

Deletes a product belonging to the authenticated user.

------------------------------------------------------------------------

# 7. Supplier APIs

## GET `/suppliers`

Returns suppliers available to the authenticated user.

Example:

``` http
GET /api/v1/suppliers
Authorization: Bearer <access_token>
```

### Typical Supplier Data

-   Supplier name
-   Contact information
-   Lead time
-   Product relationships

------------------------------------------------------------------------

## POST `/suppliers`

Creates a supplier.

The exact request fields are defined by the current FastAPI schema.

------------------------------------------------------------------------

## PUT/PATCH `/suppliers/{supplier_id}`

Updates a supplier.

------------------------------------------------------------------------

## DELETE `/suppliers/{supplier_id}`

Deletes a supplier.

------------------------------------------------------------------------

# 8. Sales APIs

## GET `/sales`

Returns historical sales records.

Example:

``` http
GET /api/v1/sales?limit=50
Authorization: Bearer <access_token>
```

Sales data is the main input for demand forecasting.

------------------------------------------------------------------------

## POST `/sales`

Adds a sales record.

Typical information:

``` json
{
  "product_id": "product-id",
  "date": "2026-08-01",
  "quantity": 15
}
```

The exact schema follows the backend implementation.

------------------------------------------------------------------------

## Sales CSV Upload

If CSV upload is enabled in the current implementation, the uploaded
data should be validated before insertion.

Typical pipeline:

``` text
CSV
 ↓
Validation
 ↓
Cleaning
 ↓
Database
 ↓
Forecasting
```

Malformed CSV data should return a clear validation error instead of
crashing the API.

------------------------------------------------------------------------

# 9. Inventory APIs

## GET `/inventory/stockout`

Returns products that are at risk of running out of stock.

Example:

``` http
GET /api/v1/inventory/stockout
Authorization: Bearer <access_token>
```

Typical information:

``` text
Product
Current Stock
Expected Demand
Stockout Risk
Estimated Days Until Stockout
```

------------------------------------------------------------------------

## GET `/inventory/overstock`

Returns products that may have excess inventory.

Example:

``` http
GET /api/v1/inventory/overstock
Authorization: Bearer <access_token>
```

Typical information:

``` text
Product
Current Stock
Forecasted Demand
Overstock Amount
Risk Level
```

------------------------------------------------------------------------

# 10. Forecasting APIs

The forecasting service analyzes historical sales and generates future
demand predictions.

The implementation uses the project's Python forecasting services,
including statistical forecasting such as **Exponential
Smoothing/Holt-Winters** where sufficient historical data is available.

### Forecast Pipeline

``` text
Historical Sales
      ↓
Data Cleaning
      ↓
Product Time Series
      ↓
Forecast Model
      ↓
Future Demand
      ↓
Inventory Analysis
```

Forecast endpoints and response schemas should be treated according to
the current FastAPI router/schema implementation.

------------------------------------------------------------------------

# 11. Alerts API

## GET `/alerts`

Returns inventory alerts for the authenticated user.

Example:

``` http
GET /api/v1/alerts?resolved=false
Authorization: Bearer <access_token>
```

### Query Parameter

``` text
resolved=false
```

Filters unresolved alerts.

### Alert Types

-   Stockout risk
-   Overstock risk
-   Other inventory warnings supported by the backend

------------------------------------------------------------------------

# 12. Reorder Recommendation API

## GET `/recommendations/reorder`

Returns products for which the system recommends replenishment.

Example:

``` http
GET /api/v1/recommendations/reorder?limit=50
Authorization: Bearer <access_token>
```

### Recommendation Logic

Conceptually:

``` text
Required Stock
= Forecasted Future Demand + Safety Stock

Suggested Reorder
= Required Stock - Current Stock
```

Supplier lead time and other inventory factors can be included by the
backend implementation.

------------------------------------------------------------------------

# 13. Authentication & Authorization

All business-data endpoints are protected.

### Required Header

``` http
Authorization: Bearer <access_token>
```

### Unauthorized Request

``` text
401 Unauthorized
```

Possible causes:

-   Missing token
-   Expired token
-   Invalid token
-   Invalid signature
-   Incorrect issuer/audience
-   Authentication session unavailable

The frontend should not bypass authentication when a 401 occurs.

------------------------------------------------------------------------

# 14. CORS

The FastAPI backend allows the configured frontend development origins.

Typical local origins:

``` text
http://localhost:5173
http://localhost:5175
http://127.0.0.1:5173
http://127.0.0.1:5175
```

Production origins should be explicitly configured.

Wildcard CORS should not be used for the authenticated application.

------------------------------------------------------------------------

# 15. HTTP Status Codes

  Status   Meaning
  -------- ---------------------------------
  200      Successful request
  201      Resource/session created
  400      Invalid request
  401      Authentication required/invalid
  403      Authenticated but not allowed
  404      Resource not found
  409      Resource conflict
  422      Validation error
  429      Rate limit exceeded
  500      Internal server error

------------------------------------------------------------------------

# 16. Error Response

FastAPI validation and application errors should return structured JSON.

Example:

``` json
{
  "detail": "Invalid request"
}
```

Frontend should convert API errors into user-friendly messages.

------------------------------------------------------------------------

# 17. Data Isolation

Every authenticated business user must only access their own:

-   Products
-   Suppliers
-   Sales
-   Forecasts
-   Alerts
-   Inventory
-   Recommendations

Supabase PostgreSQL **Row Level Security (RLS)** should be used where
applicable.

The backend must derive the authenticated user from the verified JWT
rather than trusting a user ID supplied by the frontend.

------------------------------------------------------------------------

# 18. Security Rules

Never expose:

``` text
SUPABASE_SERVICE_ROLE_KEY
```

to the React application.

It must remain on the FastAPI server.

Do not:

``` text
disable JWT verification
disable SSL verification
use wildcard JWT algorithms
disable RLS
```

Authentication and authorization must remain enabled for protected APIs.

------------------------------------------------------------------------

# 19. Complete Demo API Flow

For the RICR Bhopal hackathon demo:

``` text
POST /auth/guest
        ↓
POST /demo/seed
        ↓
GET /dashboard/summary
        ↓
GET /products
        ↓
GET /sales
        ↓
GET /inventory/stockout
        ↓
GET /inventory/overstock
        ↓
GET /alerts
        ↓
GET /recommendations/reorder
```

This produces the complete StockPilot demo experience:

``` text
Guest
 ↓
Demo Data
 ↓
Inventory
 ↓
Historical Sales
 ↓
Demand Forecast
 ↓
Stock Risk
 ↓
Reorder Recommendation
```

------------------------------------------------------------------------

# 20. API Development Notes

The definitive endpoint request/response schemas are generated by
FastAPI's OpenAPI specification.

After starting the backend, open:

``` text
http://127.0.0.1:8000/docs
```

Use Swagger UI to inspect the exact current schemas, parameters and
response models.

This document describes the application's API structure and intended
integration flow; the running FastAPI OpenAPI specification is the
source of truth for exact request/response fields.
