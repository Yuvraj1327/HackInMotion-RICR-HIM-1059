#StockPilot AI

Inventory Intelligence for Smarter Business DecisionsPredict demand. Prevent stockouts. Reduce excess inventory. Protect cash.

StockPilot AI is an AI-powered inventory intelligence platform designed to help businesses make faster, data-driven inventory decisions.

It combines inventory data, historical sales, demand forecasting, risk analysis, alerts, and reorder recommendations in one platform.

🌐 Live Application

Resource

Link

Frontend

YOUR_VERCEL_FRONTEND_URL

Backend API

YOUR_RENDER_BACKEND_URL

GitHub Repository

YOUR_GITHUB_REPOSITORY_URL

Replace the placeholders above with the final deployment URLs.

🎯 Problem

Businesses often manage inventory using spreadsheets, manual calculations, and intuition.

This can lead to:

Stockouts and missed sales

Excess inventory

Capital tied up in slow-moving products

Late identification of inventory risks

Difficult demand planning

Time-consuming manual analysis

💡 Solution

StockPilot AI turns raw inventory and sales data into clear, actionable insights.

Instead of only showing what is happening, it helps answer:

What is likely to happen next, and what should I do about it?

✨ Core Features

📊 Intelligent Dashboard

Total inventory value

Product count

Stockout risk

Overstock count

Action Center

Recent alerts

Recommended order quantities

📦 Inventory Management

Add products manually

Search by product name or SKU

Filter by category and status

Track current stock

Selling price and cost price

Lead time

Safety stock

Supplier assignment

📈 Sales Data

Upload historical sales using CSV

Manual product entry is supported

CSV is optional

Import validation

Duplicate and invalid-row detection

Historical sales used for forecasting

Supported CSV format:

date,product_id,quantity,price,promotion
2026-01-01,PRODUCT_ID,12,499,false
2026-01-02,PRODUCT_ID,15,499,true

🔮 Demand Forecasting

Forecast future product demand

Analyze historical sales patterns

Predict potential stockouts

Detect excess inventory

Support reorder decisions

🚨 Alerts

Stockout alerts

Overstock alerts

Reorder-point alerts

Risk severity levels

Recent inventory issues

💡 Recommendations

Recommended order quantities

Inventory action suggestions

Risk-based prioritization

🚚 Supplier Management

Add and manage suppliers

Lead-time tracking

Reliability information

Supplier assignment to products

🧪 Scenario Simulator

Evaluate inventory scenarios and understand how changes in demand or stock levels may affect business decisions.

🔐 Authentication & Workspaces

Supabase authentication

Private registered-user workspaces

User-specific products, sales, alerts, and inventory data

Guest/Demo experience with sample data

Data isolation: Guest Mode uses demo data. Registered users must only see data belonging to their authenticated account.

🧠 How It Works

                    ┌──────────────────┐
                    │  User / Guest    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ React Frontend   │
                    │ Vite + TypeScript│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   FastAPI API    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     Supabase     │
                    │ PostgreSQL + Auth│
                    └────────┬─────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │ Forecasting & Analysis  │
                └────────────┬────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │ Alerts • Forecasts • Actions │
              │ Recommendations • Dashboard  │
              └──────────────────────────────┘

🏗️ Architecture

HACK-IN-MOTION-RICR/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── supabase_schema.sql
│
├── architecture-diagram.png
├── README.md
└── ...

🛠️ Technology Stack

Layer

Technology

Frontend

React, TypeScript, Vite

UI

Tailwind CSS

Backend

Python, FastAPI

API Server

Uvicorn

Database

Supabase / PostgreSQL

Authentication

Supabase Auth

Forecasting

Python / Statsmodels

Frontend Deployment

Vercel

Backend Deployment

Render

🔐 Authentication & Data Flow

Registered User

Login
  ↓
Supabase Authentication
  ↓
JWT Access Token
  ↓
FastAPI
  ↓
Authenticated user_id
  ↓
User-specific data

Guest Mode

Continue as Guest
  ↓
Demo Mode
  ↓
Sample inventory + sales data
  ↓
Demo dashboard

Demo data and registered-user data are intentionally separated.

⚙️ Local Development

Prerequisites

Python 3.11+

Node.js 18+

npm

Supabase project

1. Clone

git clone YOUR_GITHUB_REPOSITORY_URL
cd HACK-IN-MOTION-RICR

2. Backend

cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

Create backend/.env:

SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
SUPABASE_JWT_SECRET=YOUR_SUPABASE_JWT_SECRET

FRONTEND_URL=http://localhost:5173
ENVIRONMENT=development

Start the API:

./.venv/bin/python -m uvicorn app.main:app --reload --port 8000

API:

http://127.0.0.1:8000

3. Frontend

cd frontend
npm install

Create frontend/.env:

VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_SUPABASE_URL=YOUR_SUPABASE_URL
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY

Start:

npm run dev

Frontend:

http://localhost:5173

☁️ Production Deployment

Frontend — Vercel

Configure:

VITE_API_BASE_URL=https://YOUR-RENDER-BACKEND-URL/api/v1
VITE_SUPABASE_URL=YOUR_SUPABASE_URL
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY

After changing Vercel environment variables, trigger a new deployment.

Backend — Render

Configure:

SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
SUPABASE_JWT_SECRET=YOUR_SUPABASE_JWT_SECRET

FRONTEND_URL=https://YOUR-VERCEL-FRONTEND-URL
ENVIRONMENT=production

Start command:

uvicorn app.main:app --host 0.0.0.0 --port $PORT

Keep FRONTEND_URL without a trailing /.

🔒 Environment & Security

Never commit secrets to GitHub.

Sensitive values include:

SUPABASE_SERVICE_ROLE_KEY
SUPABASE_JWT_SECRET

The frontend should only use the public Supabase anon key.

Recommended:

.env
.env.local

should remain ignored by Git.

📥 Sales CSV Import

Example:

date,product_id,quantity,price,promotion
2026-01-01,laptop-001,10,55000,false
2026-01-02,laptop-001,14,55000,true
2026-01-03,laptop-001,8,55000,false
2026-01-04,mouse-001,25,799,false
2026-01-05,mouse-001,31,799,true

Important:

date — sale date

product_id — existing product identifier

quantity — units sold

price — selling price

promotion — whether the sale was promotional

The product_id should match a product in the user's inventory.

🧪 Testing Checklist

Authentication

Signup

Login

Logout

Guest Mode

Session restoration

Inventory

Add product

Edit product

Search/filter

Supplier assignment

Sales

Upload valid CSV

Handle invalid CSV

Detect duplicates

View sales history

Intelligence

Dashboard metrics

Demand forecasts

Stockout predictions

Overstock detection

Alerts

Recommendations

Scenario Simulator

Data Isolation

Guest sees demo data

Registered user sees only their own data

Demo data is never automatically seeded into normal accounts

📌 Example Business Scenario

Suppose a store has:

Current Stock:      100 units
Demand Trend:       Increasing
Stockout Risk:      High
Recommended Order:  60 units

StockPilot AI turns this information into a simple decision:

Demand is increasing and inventory may run out soon. Consider ordering 60 additional units.

This helps businesses reduce lost sales while avoiding unnecessary overstock.

🚀 Value Proposition

Without StockPilot AI

Sales Data
    ↓
Spreadsheets
    ↓
Manual Analysis
    ↓
Guesswork
    ↓
Late Decisions

With StockPilot AI

Sales + Inventory
       ↓
Automated Analysis
       ↓
Demand Forecast
       ↓
Risk Detection
       ↓
Actionable Recommendation

Predict demand → Detect risk → Recommend action → Protect cash.

🏆 Project Information

Project: StockPilot AICategory: AI / Inventory IntelligenceTagline: Inventory IntelligenceFrontend: React + ViteBackend: FastAPIDatabase: SupabaseDeployment: Vercel + Render

🔗 Project Links

Live Application: YOUR_VERCEL_FRONTEND_URL

Backend API: YOUR_RENDER_BACKEND_URL

Source Code: YOUR_GITHUB_REPOSITORY_URL

📄 License

Add the project's preferred license here.

👨‍💻 Development

Built as an AI-powered inventory intelligence platform focused on making demand planning and inventory decisions faster, clearer, and more actionable.