# StockPilot AI

> ## Inventory Intelligence for Smarter Business Decisions

**StockPilot AI** is an AI-powered inventory intelligence platform designed to help businesses manage inventory, analyze sales, forecast demand, detect stock risks, and make smarter purchasing decisions.

### Predict Demand. Prevent Stockouts. Reduce Overstock. Protect Cash.

---

# 🌐 Live Application

| Resource | Link |
|---|---|
| 🌍 Live Website | `https://hack-in-motion-ricr-him-1059.vercel.app` |
| ⚡ Backend API | `https://hackinmotion-ricr-him-1059-backend.onrender.com/` |
| 📚 API Documentation | `https://hackinmotion-ricr-him-1059-backend.onrender.com/L/docs` |
| 💻 GitHub Repository | `https://github.com/Yuvraj1327/HackInMotion-RICR-HIM-1059` |

> Replace the placeholder URLs with your actual deployment links.

---

# 🎯 Overview

Inventory management becomes difficult when businesses rely on spreadsheets, manual calculations, and assumptions.

StockPilot AI provides a centralized platform where businesses can manage inventory and sales data while receiving intelligent insights about future demand and inventory risks.

The platform combines:

- Inventory Management
- Sales Management
- Demand Forecasting
- Stockout Prediction
- Overstock Detection
- Smart Alerts
- Reorder Recommendations
- Supplier Management
- Scenario Simulation
- Guest Demo Mode
- Secure User Authentication

---

# ❗ Problem

Traditional inventory management can create several problems:

- Products go out of stock unexpectedly
- Businesses purchase more inventory than required
- Working capital gets locked in excess stock
- Demand trends are difficult to identify
- Sales data is underutilized
- Manual analysis takes significant time
- Purchasing decisions are often based on guesswork
- Inventory risks are identified too late

---

# 💡 Solution

StockPilot AI converts raw inventory and sales data into actionable insights.

Instead of simply showing numbers, the platform helps answer:

```text
What is happening?
        ↓
What is likely to happen next?
        ↓
What should the business do?
```

This allows businesses to move from reactive inventory management to proactive, data-driven decision making.

---

# ✨ Key Features

## 📊 Intelligent Dashboard

The dashboard provides a centralized view of inventory health.

### Dashboard Metrics

- Total Inventory Value
- Total Products
- Stockout Risk
- Overstock Count
- Inventory Health
- Sales Overview
- Recent Alerts
- Action Center
- Reorder Recommendations
- Demand Insights

---

## 📦 Inventory Management

StockPilot AI allows businesses to manage their products and inventory from one place.

### Product Management

- Add products manually
- Edit products
- Search products
- Filter products
- Manage SKU
- Track stock quantity
- Track selling price
- Track cost price
- Configure lead time
- Configure safety stock
- Assign suppliers
- Monitor inventory status

### Manual Data Entry

Users do not need a CSV file to start using the platform.

Products and inventory can be entered manually.

> **CSV upload is optional.**

---

# 📈 Sales Management

Historical sales data can be used to improve demand forecasting.

StockPilot AI supports:

- Sales history
- Manual data entry
- CSV import
- CSV validation
- Duplicate detection
- Invalid-row detection
- Historical sales analysis

---

# 📥 CSV Import

Users can optionally upload historical sales data using CSV.

### Example CSV

```csv
date,product_id,quantity,price,promotion
2026-01-01,laptop-001,10,55000,false
2026-01-02,laptop-001,14,55000,true
2026-01-03,laptop-001,8,55000,false
2026-01-04,mouse-001,25,799,false
2026-01-05,mouse-001,31,799,true
```

### CSV Fields

| Field | Description |
|---|---|
| `date` | Date of the sale |
| `product_id` | Existing product identifier |
| `quantity` | Number of units sold |
| `price` | Selling price |
| `promotion` | Whether the sale was promotional |

---

# 🔮 AI Demand Forecasting

StockPilot AI analyzes historical sales patterns to estimate future demand.

### Forecasting Capabilities

- Historical sales analysis
- Demand trend detection
- Future demand forecasting
- Stockout prediction
- Overstock detection
- Inventory planning
- Reorder planning

---

# 🚨 Smart Inventory Alerts

StockPilot AI identifies products that require attention.

### Alert Types

- Stockout Risk
- Overstock Risk
- Reorder Required
- Inventory Warning
- High-Risk Product
- Recent Inventory Alert

---

# 💡 Reorder Recommendations

The platform provides recommended purchasing quantities based on inventory and demand information.

### Example

```text
Current Stock:        100 units
Average Demand:        18 units/day
Demand Trend:         Increasing
Stockout Risk:        High
Recommended Order:     60 units
```

> Demand is increasing and the product may run out soon. Consider ordering 60 additional units.

---

# 🚚 Supplier Management

Businesses can manage suppliers and connect them with products.

### Supplier Features

- Add suppliers
- Edit suppliers
- Supplier contact information
- Track lead time
- Track reliability
- Assign suppliers to products
- View supplier information

---

# 🧪 Scenario Simulator

The Scenario Simulator allows users to test different inventory situations.

Users can experiment with:

- Demand changes
- Stock changes
- Sales volume
- Reorder quantities

---

# 👻 Guest Mode

StockPilot AI includes a dedicated Guest Mode for instant product demonstration.

Guest users can explore the platform using sample inventory and sales data without creating a business account.

### Guest Flow

```text
Continue as Guest
        ↓
Demo Account
        ↓
Demo Products + Sales
        ↓
Demo Dashboard
        ↓
Explore StockPilot AI
```

---

# 🔐 Authentication

StockPilot AI uses Supabase Authentication for secure account management.

### Supported Authentication

- Signup
- Login
- Logout
- Session Restoration
- JWT Authentication
- Guest Mode
- Private User Workspace

---

# 🔒 Data Isolation

## Guest Account

```text
Guest
  ↓
Demo Account
  ↓
Demo Data
```

## Registered Account

```text
Registered User
  ↓
Authenticated Account
  ↓
User ID
  ↓
Own Products
  ↓
Own Sales
  ↓
Own Suppliers
  ↓
Own Alerts
  ↓
Own Inventory
```

### Important Rule

**Real registered accounts must NEVER automatically receive demo or seed data.**

Every registered user should only see data associated with their authenticated account.

---

# 🧠 System Architecture

```text
                    ┌──────────────────┐
                    │   User / Guest   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ React Frontend   │
                    │ TypeScript/Vite  │
                    └────────┬─────────┘
                             │
                         REST API
                             │
                             ▼
                    ┌──────────────────┐
                    │ FastAPI Backend  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    Supabase      │
                    │ PostgreSQL + Auth│
                    └────────┬─────────┘
                             │
                             ▼
              ┌────────────────────────────┐
              │ Forecasting & Inventory    │
              │ Analysis Services          │
              └─────────────┬──────────────┘
                            │
                            ▼
             ┌─────────────────────────────┐
             │ Dashboard • Alerts          │
             │ Forecasts • Recommendations │
             └─────────────────────────────┘
```

---

# 🔄 Application Flow

```text
User Login / Guest
        ↓
Authentication
        ↓
JWT Session
        ↓
Frontend API Request
        ↓
FastAPI Backend
        ↓
User Authentication
        ↓
Supabase PostgreSQL
        ↓
Inventory + Sales Data
        ↓
Forecasting
        ↓
Risk Analysis
        ↓
Alerts + Recommendations
        ↓
Dashboard
```

---

# 🏗️ Project Structure

```text
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
│   │
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── supabase_schema.sql
│
├── README.md
└── ...
```

---

# 🛠️ Technology Stack

| Category | Technology |
|---|---|
| Frontend | React |
| Language | TypeScript |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| Backend | Python |
| API Framework | FastAPI |
| API Server | Uvicorn |
| Database | PostgreSQL |
| Backend Platform | Supabase |
| Authentication | Supabase Auth |
| Forecasting | Statsmodels |
| Frontend Hosting | Vercel |
| Backend Hosting | Render |

---

# ⚙️ Local Development

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm
- Git
- Supabase Project

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Backend: `http://127.0.0.1:8000`

Swagger: `http://127.0.0.1:8000/docs`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

---

# 🔑 Environment Variables

## Frontend

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_SUPABASE_URL=YOUR_SUPABASE_URL
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
```

## Backend

```env
SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
SUPABASE_JWT_SECRET=YOUR_SUPABASE_JWT_SECRET
FRONTEND_URL=http://localhost:5173
ENVIRONMENT=development
```

---

# ☁️ Production Deployment

```text
Frontend → Vercel
Backend  → Render
Database → Supabase
Auth     → Supabase Auth
```

### Render Start Command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

> Keep `FRONTEND_URL` without a trailing `/`.

---

# 🔒 Security

Never commit private credentials to GitHub.

Sensitive variables include:

```text
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_JWT_SECRET
```

Never expose these in frontend code or browser environments.

Recommended `.gitignore`:

```text
.env
.env.local
.env.*.local
```

---

# 📡 API

The FastAPI backend provides REST APIs for:

- Authentication
- Products
- Sales
- Suppliers
- Inventory
- Forecasting
- Alerts
- Recommendations
- Dashboard
- Guest/Demo functionality

### Production API

`https://github.com/Yuvraj1327/HackInMotion-RICR-HIM-1059`

### Swagger

`https://github.com/Yuvraj1327/HackInMotion-RICR-HIM-1059L/docs`

---

# 📥 Sales CSV Example

```csv
date,product_id,quantity,price,promotion
2026-01-01,laptop-001,10,55000,false
2026-01-02,laptop-001,14,55000,true
2026-01-03,laptop-001,8,55000,false
2026-01-04,mouse-001,25,799,false
2026-01-05,mouse-001,31,799,true
```

| Field | Meaning |
|---|---|
| `date` | Sale date |
| `product_id` | Existing product identifier |
| `quantity` | Units sold |
| `price` | Selling price |
| `promotion` | Promotional sale status |

> CSV upload is optional. Sales can also be entered manually.

---

# 🧪 Testing Checklist

## Authentication

- [ ] Signup
- [ ] Login
- [ ] Logout
- [ ] Guest Mode
- [ ] Session restoration
- [ ] JWT authentication
- [ ] Token refresh
- [ ] Expired-session handling

## Dashboard

- [ ] Dashboard loads correctly
- [ ] No infinite skeleton/loading
- [ ] Inventory metrics are correct
- [ ] Sales metrics are correct
- [ ] Alerts load correctly
- [ ] Recommendations load correctly
- [ ] Loading states work
- [ ] Error states work
- [ ] Empty states work

## Inventory

- [ ] Add product
- [ ] Edit product
- [ ] Delete product
- [ ] Search product
- [ ] Filter products
- [ ] Update stock
- [ ] Assign supplier

## Sales

- [ ] Add sales
- [ ] Upload CSV
- [ ] Validate CSV
- [ ] Handle invalid rows
- [ ] Detect duplicates
- [ ] View sales history
- [ ] Verify user ownership

## AI

- [ ] Demand forecast
- [ ] Stockout prediction
- [ ] Overstock analysis
- [ ] Reorder recommendations
- [ ] Scenario Simulator

## Data Isolation

- [ ] Guest receives demo data
- [ ] Guest receives demo alerts
- [ ] Real user receives only private data
- [ ] Real user never receives demo/seed data automatically
- [ ] User A cannot access User B data

---

# 📊 Example Business Scenario

```text
Current Stock:        100 units
Average Demand:        18 units/day
Demand Trend:         Increasing
Stockout Risk:        High
Recommended Order:     60 units
```

StockPilot AI turns this into an actionable recommendation:

> **Demand is increasing and the product may run out soon. Consider ordering 60 additional units.**

---

# 💼 Business Value

StockPilot AI can help businesses:

- Reduce stockouts
- Reduce excess inventory
- Improve demand planning
- Save working capital
- Reduce manual work
- Identify risks earlier
- Improve purchasing decisions
- Improve inventory visibility
- Make data-driven decisions

---

# 🔄 Traditional vs StockPilot AI

## Traditional Process

```text
Sales Data
    ↓
Spreadsheet
    ↓
Manual Calculations
    ↓
Manual Analysis
    ↓
Guesswork
    ↓
Delayed Decision
```

## StockPilot AI

```text
Sales + Inventory
       ↓
Automated Analysis
       ↓
Demand Forecast
       ↓
Risk Detection
       ↓
Smart Alert
       ↓
Reorder Recommendation
       ↓
Business Action
```

---

# 🎯 Target Users

StockPilot AI can be useful for:

- Retail Shops
- Supermarkets
- Small Businesses
- Wholesalers
- Distributors
- E-commerce Sellers
- Local Stores
- Inventory-Based Businesses

---

# 🏪 Real-World Use Case

A shop owner manages hundreds of products.

Instead of manually checking spreadsheets every day:

```text
Add Products
      ↓
Add Sales
      ↓
Upload Historical CSV (Optional)
      ↓
StockPilot Analyzes Data
      ↓
Demand Forecast
      ↓
Risk Detection
      ↓
Alerts
      ↓
Reorder Recommendations
      ↓
Business Decision
```

---

# 💰 Business Impact

StockPilot AI focuses on two major inventory problems:

```text
Too Little Inventory
        ↓
Stockout
        ↓
Lost Sales
```

and:

```text
Too Much Inventory
        ↓
Overstock
        ↓
Capital Locked
```

The goal is to help businesses maintain a healthier inventory balance.

---

# 📌 Core Product Philosophy

```text
Understand
    ↓
Predict
    ↓
Detect
    ↓
Recommend
    ↓
Act
```

---

# 🧩 Main Modules

| Module | Purpose |
|---|---|
| Dashboard | Business overview |
| Inventory | Product and stock management |
| Sales | Sales history and import |
| Forecasting | Future demand estimation |
| Alerts | Inventory risk notifications |
| Recommendations | Suggested inventory actions |
| Suppliers | Supplier management |
| Simulator | Scenario analysis |
| Authentication | User access and security |
| Guest Mode | Product demonstration |

---

# 🔄 Data Flow

```text
Product Data
     +
Sales Data
     +
Supplier Data
     ↓
Supabase PostgreSQL
     ↓
FastAPI Services
     ↓
Forecasting
     ↓
Inventory Analysis
     ↓
Risk Detection
     ↓
Recommendations
     ↓
Frontend Dashboard
```

---

# ⚡ Performance

The dashboard should avoid unnecessary API requests.

Performance considerations include:

- Reusing dashboard summary APIs
- Avoiding unnecessary sequential requests
- Batching data where possible
- Loading independent data concurrently
- Preventing duplicate requests
- Avoiding repeated authentication calls

---

# 🔁 Error Handling

The application should properly handle:

- Network errors
- Authentication errors
- Expired tokens
- Invalid data
- Empty datasets
- API errors
- Database errors
- CSV validation errors

Users should receive a useful error state instead of being left on an infinite loading screen.

---

# 🟢 Production Checklist

- [ ] Frontend deployed on Vercel
- [ ] Backend deployed on Render
- [ ] Supabase configured
- [ ] Environment variables configured
- [ ] CORS configured
- [ ] Authentication tested
- [ ] Guest Mode tested
- [ ] Real account tested
- [ ] Data isolation verified
- [ ] Dashboard tested
- [ ] CSV import tested
- [ ] Forecasting tested
- [ ] Alerts tested
- [ ] Recommendations tested
- [ ] API documentation available
- [ ] Secrets removed from source code
- [ ] Production URLs configured

---



# 🏆 Project Information

| Property | Details |
|---|---|
| Project Name | StockPilot AI |
| Tagline | Inventory Intelligence |
| Category | AI / Inventory Management |
| Frontend | React + TypeScript + Vite |
| Backend | FastAPI + Python |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| Forecasting | Statsmodels |
| Frontend Hosting | Vercel |
| Backend Hosting | Render |

---

# 🎓 Project Objective

The objective of StockPilot AI is to make inventory management more intelligent and accessible for small and medium-sized businesses.

Instead of requiring complex enterprise software or manual spreadsheets, StockPilot AI provides a simple interface for:

```text
Manage Inventory
       ↓
Analyze Sales
       ↓
Forecast Demand
       ↓
Identify Risks
       ↓
Get Recommendations
       ↓
Make Better Decisions
```

---

# 🌟 Why StockPilot AI?

Traditional inventory systems often tell businesses what their inventory looks like today.

StockPilot AI focuses on helping businesses understand what may happen next.

```text
Traditional System
        ↓
Current Status

StockPilot AI
        ↓
Current Status
        +
Future Demand
        +
Risk
        +
Recommended Action
```

---

# 🚀 Key Value Proposition

```text
Predict Demand
      ↓
Detect Inventory Risk
      ↓
Recommend Action
      ↓
Protect Cash
```

> **StockPilot AI turns inventory data into smarter business decisions.**

---

# 🏁 Conclusion

StockPilot AI provides a complete inventory intelligence workflow for businesses that want better visibility and smarter purchasing decisions.

From manually adding products to uploading historical sales, forecasting demand, detecting inventory risks, and receiving reorder recommendations, the platform brings the complete workflow into one system.

### StockPilot AI

> **Inventory Intelligence — Smarter Stock. Smarter Decisions.**

---


# 📄 License

This project is developed for demonstration, learning, hackathon, and potential business use.

Add the preferred open-source or proprietary license here.

---

# 👨‍💻 Development

StockPilot AI was developed as an AI-powered inventory intelligence platform focused on helping businesses understand inventory, analyze sales, forecast demand, identify risks, and make better purchasing decisions.

## StockPilot AI

### **Inventory Intelligence for Smarter Business Decisions******
