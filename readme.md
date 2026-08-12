# StockPilot AI

> **AI-Powered Inventory & Demand Forecasting System**
>
> Because empty shelves lose sales, and overstocked shelves lose money.

StockPilot AI is a full-stack inventory intelligence platform designed
for small and mid-sized retailers and e-commerce businesses. It helps
business owners understand current inventory, analyze historical sales,
forecast future demand, identify stockout/overstock risks, and make
smarter reorder decisions.

## 🚀 Problem

Retailers often make stocking decisions using guesswork or spreadsheets.
Ordering too little can cause stockouts and lost sales, while ordering
too much ties up cash and increases storage or wastage costs.

StockPilot turns historical sales and inventory data into actionable
recommendations.

## 💡 Solution

StockPilot provides:

-   Secure business-user authentication
-   Product and inventory management
-   Supplier management
-   Historical sales data handling
-   Data-driven demand forecasting
-   Stockout and overstock alerts
-   Automated reorder recommendations
-   Analytics dashboard
-   Demo/Guest Mode for instant hackathon demonstration
-   Persistent PostgreSQL storage through Supabase

## ✨ Key Features

### 1. Authentication

-   Secure signup/login
-   Supabase Auth
-   Guest/Demo Mode
-   User-specific data access
-   JWT-based authentication between frontend and FastAPI

### 2. Inventory Management

Users can: - Add products - Edit products - Delete products - View stock
levels - Track price/category/supplier information

### 3. Sales Data

Historical sales can be used as the forecasting input.

The platform is designed to support: - CSV sales uploads - Demo/sample
sales data - Persistent sales history

### 4. Demand Forecasting

StockPilot analyzes historical sales to estimate future product demand.

The forecasting engine is implemented in Python and can use statistical
forecasting techniques such as Exponential Smoothing depending on the
available data.

The system is designed to: - Detect recent sales trends - Estimate
future demand - Generate product-level forecasts - Handle
limited/insufficient historical data gracefully

### 5. Smart Inventory Alerts

StockPilot identifies:

**Stockout Risk** - Current stock may not cover expected future demand.

**Overstock Risk** - Current inventory is significantly higher than
expected demand.

**Reorder Recommendation** - Suggests when a product should be reordered
and the approximate quantity required.

### 6. Analytics Dashboard

The dashboard provides an at-a-glance view of:

-   Total products
-   Inventory status
-   Stockout risks
-   Overstock risks
-   Sales trends
-   Demand forecasts
-   Alerts
-   Reorder recommendations

The goal is to help a business owner make a decision in seconds.

## 🏗️ Architecture

``` text
                 ┌──────────────────────┐
                 │      React UI        │
                 │  Dashboard / Forms   │
                 └──────────┬───────────┘
                            │ REST API
                            ▼
                 ┌──────────────────────┐
                 │      FastAPI         │
                 │ Auth / Business      │
                 │ Logic / Forecasting  │
                 └──────────┬───────────┘
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
   ┌──────────────────┐          ┌──────────────────┐
   │  Supabase Auth   │          │ Supabase         │
   │  JWT / Users     │          │ PostgreSQL       │
   └──────────────────┘          │ Inventory/Sales  │
                                 │ Forecasts/Alerts  │
                                 └──────────────────┘
```

## 🛠️ Tech Stack

### Frontend

-   React
-   TypeScript
-   Vite
-   Axios
-   React Query (if enabled in the project)
-   Charting library used by the project

### Backend

-   Python
-   FastAPI
-   Uvicorn
-   Pydantic
-   Pandas
-   NumPy
-   Statsmodels
-   JWT authentication

### Database & Authentication

-   Supabase
-   PostgreSQL
-   Supabase Auth
-   Row Level Security (RLS)

### Forecasting

-   Python-based statistical forecasting
-   Exponential Smoothing / Holt-Winters where applicable
-   Rule-based inventory calculations for stockout, overstock and
    reorder decisions

## 📁 Project Structure

``` text
StockPilot/
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── ...
│
├── architecture-diagram.png
├── api-documentation.md
├── presentation.pptx
└── README.md
```

## ⚙️ Local Setup

### Prerequisites

Install:

-   Node.js
-   npm
-   Python 3.11+
-   Supabase account

### 1. Clone Repository

``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd StockPilot
```

### 2. Backend Setup

``` bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:

``` env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

FRONTEND_URL=http://localhost:5173
```

Start FastAPI:

``` bash
./.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Backend:

``` text
http://127.0.0.1:8000
```

API documentation:

``` text
http://127.0.0.1:8000/docs
```

### 3. Frontend Setup

``` bash
cd frontend
npm install
```

Create `.env`:

``` env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Start frontend:

``` bash
npm run dev
```

Open the Vite URL shown in the terminal.

## 🗄️ Supabase Database Setup

Create a Supabase project and run the database SQL/migrations included
with the project.

The database should contain the tables required by the current backend,
including the project entities for:

-   Profiles
-   Products
-   Suppliers
-   Sales
-   Forecasts
-   Alerts
-   Reorder recommendations
-   Other supporting inventory entities

Make sure the schema matches the FastAPI repositories and models.

### Security

Row Level Security should ensure that authenticated users can only
access their own business data.

The Supabase Service Role Key must only be used on the backend and must
never be exposed in the React frontend.

## 👤 Guest / Demo Mode

StockPilot includes a Guest Mode specifically for quick product
demonstrations.

Flow:

``` text
Continue as Guest
        ↓
Create/reuse demo session
        ↓
Seed realistic demo data
        ↓
Generate/load forecasts
        ↓
Show dashboard
        ↓
Show alerts + reorder recommendations
```

Guest Mode allows judges to experience the product without creating a
real business account.

Demo data should remain isolated from normal users.

## 📊 Forecasting Approach

StockPilot uses a data-driven forecasting pipeline rather than
generating random numbers.

The forecasting engine can evaluate historical sales and use statistical
forecasting such as Exponential Smoothing/Holt-Winters when enough data
is available.

A typical flow is:

``` text
Historical Sales
       ↓
Data Cleaning
       ↓
Daily/Product Aggregation
       ↓
Trend & Seasonality Analysis
       ↓
Forecast Model
       ↓
Future Demand
       ↓
Inventory Risk Analysis
       ↓
Reorder Recommendation
```

For products with insufficient historical data, the system should use an
appropriate fallback strategy instead of producing unreliable forecasts.

## 🧠 Smart Reorder Logic

The system combines:

-   Current stock
-   Forecasted demand
-   Expected demand horizon
-   Safety stock / buffer
-   Supplier lead time where available

Conceptually:

``` text
Required Stock
= Expected Future Demand
+ Safety Stock

Suggested Reorder
= Required Stock - Current Stock
```

The exact implementation follows the backend's inventory/recommendation
services.

## 🔔 Alerts

Examples:

### High Stockout Risk

``` text
Wireless Mouse
Current Stock: 12
Expected 7-Day Demand: 25

⚠ Reorder recommended
```

### Overstock Risk

``` text
Winter Jacket
Current Stock: 180
Expected 30-Day Demand: 70

⚠ Overstock detected
Consider promotion/discounting
```

## 📥 Sales Data Pipeline

Supported demonstration flow:

``` text
CSV / Demo Sales Data
        ↓
Validation
        ↓
Data Cleaning
        ↓
Database Storage
        ↓
Forecasting Engine
        ↓
Forecast Results
        ↓
Alerts & Recommendations
```

Malformed or incomplete uploads should return a clear user-facing error
instead of breaking the dashboard.

## 🔐 Security

StockPilot follows these principles:

-   JWT authentication
-   User-specific authorization
-   Supabase RLS
-   Service-role credentials kept on the backend
-   No hardcoded secrets
-   Explicit CORS configuration
-   Protected API endpoints
-   Input validation
-   Error handling for failed requests

## 🧪 Testing Checklist

Before a demo, verify:

### Backend

``` bash
./.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Check:

``` text
GET /
GET /docs
```

### Guest Demo

``` text
Continue as Guest
→ Demo seed
→ Dashboard
→ Products
→ Sales
→ Forecasts
→ Alerts
→ Reorder Recommendations
```

### Normal User

``` text
Signup
→ Login
→ Add Product
→ Add/Upload Sales
→ Generate Forecast
→ View Alerts
→ View Reorder Recommendation
→ Logout
```

## 🚀 Deployment

Recommended deployment architecture:

``` text
React Frontend
      ↓
Vercel / Netlify
      ↓
FastAPI Backend
      ↓
Render / Railway / AWS
      ↓
Supabase
```

Production environment variables must be configured in the deployment
platforms.

Never commit `.env` files containing real credentials.

## 🎯 Real-World Impact

StockPilot is designed to make demand forecasting accessible to small
and mid-sized businesses that cannot afford expensive enterprise
inventory-management systems.

Potential benefits:

-   Fewer stockouts
-   Lower excess inventory
-   Better purchasing decisions
-   Reduced working-capital lockup
-   Lower product wastage
-   Faster business decision-making

## 🔮 Future Scope

### Seasonal & Festival Intelligence

Integrate festival calendars and seasonal patterns into forecasting.

### Multi-Location Inventory

Support multiple stores, warehouses and stock transfers.

### Price Optimization

Suggest discounts for slow-moving products.

### Automated Purchase Orders

Generate supplier purchase orders when reorder thresholds are reached.

### What-If Simulation

Example:

``` text
"What if demand increases by 20% next month?"
```

The system can simulate the impact on inventory and reorder
requirements.

### External Signals

Future versions can incorporate: - Weather - Promotions - Holidays -
Market trends - Local demand patterns

## 🏆 Hackathon Demo Flow

For the RICR Bhopal hackathon, the recommended live demo is:

``` text
1. Open StockPilot
2. Continue as Guest
3. Demo data loads
4. Show dashboard
5. Pick a high-demand product
6. Show forecast graph
7. Show predicted stockout
8. Show exact reorder recommendation
9. Show an overstock product
10. Explain how the business owner can act immediately
```

The key pitch is:

> **StockPilot doesn't just show inventory numbers --- it predicts what
> will happen next and tells the business owner what to do.**

## 👥 Team

**Project:** StockPilot AI\
**Hackathon:** RICR Bhopal -- HackInMotion

Add team member names, GitHub profiles and roles here.

## 📄 Required Deliverables

-   `README.md`
-   `architecture-diagram.png`
-   `api-documentation.md`
-   `presentation.pptx`
-   Deployed frontend
-   Deployed backend
-   GitHub repository

## 📜 License

This project was created for the RICR Bhopal hackathon.
