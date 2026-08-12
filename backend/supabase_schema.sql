-- ============================================================================
-- StockPilot AI - Supabase PostgreSQL schema + Row Level Security policies
--
-- Run this in the Supabase SQL editor (Dashboard -> SQL Editor -> New query)
-- against a fresh project, or via `supabase db push` / the CLI migration
-- workflow. Safe to re-run: uses IF NOT EXISTS / CREATE OR REPLACE where
-- possible.
-- ============================================================================

create extension if not exists "pgcrypto"; -- for gen_random_uuid()

-- ----------------------------------------------------------------------------
-- profiles
-- One row per authenticated user, id == auth.users.id
-- ----------------------------------------------------------------------------
create table if not exists profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null,
    business_name text not null default '',
    created_at timestamptz not null default now()
);

alter table profiles enable row level security;

drop policy if exists "profiles_select_own" on profiles;
create policy "profiles_select_own" on profiles
    for select using (auth.uid() = id);

drop policy if exists "profiles_insert_own" on profiles;
create policy "profiles_insert_own" on profiles
    for insert with check (auth.uid() = id);

drop policy if exists "profiles_update_own" on profiles;
create policy "profiles_update_own" on profiles
    for update using (auth.uid() = id);

-- ----------------------------------------------------------------------------
-- suppliers
-- ----------------------------------------------------------------------------
create table if not exists suppliers (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    name text not null,
    contact_name text,
    email text,
    phone text,
    lead_time_days integer not null default 3 check (lead_time_days >= 0),
    reliability_score numeric not null default 0.9 check (reliability_score >= 0 and reliability_score <= 1),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_suppliers_user_id on suppliers(user_id);

alter table suppliers enable row level security;

drop policy if exists "suppliers_all_own" on suppliers;
create policy "suppliers_all_own" on suppliers
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- products
-- ----------------------------------------------------------------------------
create table if not exists products (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    name text not null,
    sku text not null,
    category text not null,
    current_stock integer not null default 0 check (current_stock >= 0),
    price numeric not null check (price > 0),
    cost_price numeric not null check (cost_price > 0),
    supplier_id uuid references suppliers(id) on delete set null,
    lead_time_days integer not null default 3 check (lead_time_days >= 0 and lead_time_days <= 365),
    safety_stock integer not null default 0 check (safety_stock >= 0),
    unit text not null default 'unit',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, sku)
);

create index if not exists idx_products_user_id on products(user_id);
create index if not exists idx_products_category on products(user_id, category);

alter table products enable row level security;

drop policy if exists "products_all_own" on products;
create policy "products_all_own" on products
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- sales
-- ----------------------------------------------------------------------------
create table if not exists sales (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    product_id uuid not null references products(id) on delete cascade,
    sale_date date not null,
    quantity integer not null check (quantity >= 0),
    unit_price numeric not null default 0 check (unit_price >= 0),
    promotion boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists idx_sales_user_id on sales(user_id);
create index if not exists idx_sales_product_id on sales(product_id);
create index if not exists idx_sales_product_date on sales(product_id, sale_date);

alter table sales enable row level security;

drop policy if exists "sales_all_own" on sales;
create policy "sales_all_own" on sales
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- forecasts
-- ----------------------------------------------------------------------------
create table if not exists forecasts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    product_id uuid not null references products(id) on delete cascade,
    forecast_date date not null,
    predicted_demand numeric not null,
    lower_bound numeric not null,
    upper_bound numeric not null,
    model_name text not null,
    confidence numeric not null check (confidence >= 0 and confidence <= 1),
    created_at timestamptz not null default now()
);

create index if not exists idx_forecasts_user_id on forecasts(user_id);
create index if not exists idx_forecasts_product_id on forecasts(product_id);

alter table forecasts enable row level security;

drop policy if exists "forecasts_all_own" on forecasts;
create policy "forecasts_all_own" on forecasts
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- forecast_runs (model evaluation metadata / audit trail)
-- ----------------------------------------------------------------------------
create table if not exists forecast_runs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    product_id uuid not null references products(id) on delete cascade,
    model_name text not null,
    training_records integer not null default 0,
    forecast_horizon integer not null,
    mae numeric,
    rmse numeric,
    mape numeric,
    created_at timestamptz not null default now()
);

create index if not exists idx_forecast_runs_user_id on forecast_runs(user_id);
create index if not exists idx_forecast_runs_product_id on forecast_runs(product_id);

alter table forecast_runs enable row level security;

drop policy if exists "forecast_runs_all_own" on forecast_runs;
create policy "forecast_runs_all_own" on forecast_runs
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- alerts
-- ----------------------------------------------------------------------------
create table if not exists alerts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    product_id uuid references products(id) on delete cascade,
    alert_type text not null check (alert_type in (
        'STOCKOUT', 'LOW_STOCK', 'OVERSTOCK', 'DEMAND_SPIKE', 'DEMAND_DROP', 'DATA_ANOMALY'
    )),
    severity text not null check (severity in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    title text not null,
    message text not null,
    recommended_action text,
    resolved boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists idx_alerts_user_id on alerts(user_id);
create index if not exists idx_alerts_product_id on alerts(product_id);
create index if not exists idx_alerts_resolved on alerts(user_id, resolved);

alter table alerts enable row level security;

drop policy if exists "alerts_all_own" on alerts;
create policy "alerts_all_own" on alerts
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- events (optional: festival/seasonal support, modular for future use)
-- ----------------------------------------------------------------------------
create table if not exists events (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    name text not null,
    start_date date not null,
    end_date date not null,
    category text,
    uplift_factor numeric check (uplift_factor > 0),
    created_at timestamptz not null default now()
);

create index if not exists idx_events_user_id on events(user_id);

alter table events enable row level security;

drop policy if exists "events_all_own" on events;
create policy "events_all_own" on events
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- updated_at trigger helper (products, suppliers)
-- ----------------------------------------------------------------------------
create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_products_updated_at on products;
create trigger trg_products_updated_at
    before update on products
    for each row execute function set_updated_at();

drop trigger if exists trg_suppliers_updated_at on suppliers;
create trigger trg_suppliers_updated_at
    before update on suppliers
    for each row execute function set_updated_at();

-- ============================================================================
-- Notes:
-- - The backend uses the SERVICE ROLE key (which bypasses RLS) so it can
--   perform its own JWT-verified authorization. Every repository query in
--   the backend still explicitly filters by user_id as defense-in-depth,
--   so RLS above is a second, independent enforcement layer - not the only
--   one - matching the "never rely only on frontend restrictions" and
--   "backend/database must enforce data isolation" requirements.
-- - If/when the frontend ever queries Supabase directly with the user's own
--   session (anon key + user JWT), these RLS policies alone are sufficient
--   to keep data isolated per user.
-- ============================================================================
