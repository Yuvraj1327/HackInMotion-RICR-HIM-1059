////deshboard.tsx

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Wallet,
  Package,
  AlertTriangle,
  PackageX,
  Rocket,
  Upload,
  ArrowRight,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { RiskBadge } from "@/components/common/StatusBadges";
import { GenerateDemoDialog } from "@/components/dashboard/GenerateDemoDialog";
import { getDashboardSummary } from "@/api/dashboard";
import { QUERY_KEYS } from "@/lib/constants";
import { formatCurrency, formatNumber } from "@/lib/utils";
import { ApiError } from "@/api/client";

function MetricCard({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string;
  icon: typeof Wallet;
  accent: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="mt-1 text-2xl font-semibold text-foreground">{value}</p>
        </div>
        <div className={`flex h-10 w-10 items-center justify-center rounded-full ${accent}`}>
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [demoOpen, setDemoOpen] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: QUERY_KEYS.dashboard,
    queryFn: getDashboardSummary,
  });

  const hasNoProducts = !isLoading && !isError && data && data.total_products === 0;

  return (
    <AppShell title="Dashboard">
      <div className="space-y-6">
        {hasNoProducts && (
          <Card className="border-primary/20 bg-primary/[0.03]">
            <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
              <Rocket className="h-9 w-9 text-primary" />
              <div>
                <h2 className="text-lg font-semibold text-foreground">🚀 New to StockPilot?</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Generate a realistic demo store or upload your own sales history to get started.
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-3">
                <Button onClick={() => setDemoOpen(true)}>
                  <Rocket className="h-4 w-4" />
                  Generate Demo Store
                </Button>
                <Link to="/sales">
                  <Button variant="outline">
                    <Upload className="h-4 w-4" />
                    Upload Sales CSV
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}

        {isLoading && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        )}

        {isError && (
          <ErrorState
            message={error instanceof ApiError ? error.message : "Unable to load dashboard data."}
            onRetry={() => refetch()}
          />
        )}

        {data && (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard
                label="Total Inventory Value"
                value={formatCurrency(data.inventory_value)}
                icon={Wallet}
                accent="bg-primary/10 text-primary"
              />
              <MetricCard
                label="Products"
                value={formatNumber(data.total_products)}
                icon={Package}
                accent="bg-muted text-foreground"
              />
              <MetricCard
                label="Stockout Risk"
                value={formatNumber(data.stockout_risk_products)}
                icon={AlertTriangle}
                accent="bg-critical/10 text-critical"
              />
              <MetricCard
                label="Overstock"
                value={formatNumber(data.overstock_products)}
                icon={PackageX}
                accent="bg-overstock/10 text-overstock"
              />
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card className="lg:col-span-2">
                <CardHeader className="flex-row items-center justify-between">
                  <CardTitle className="text-base">Action Center</CardTitle>
                  <Link to="/recommendations">
                    <Button variant="ghost" size="sm">
                      View all <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                </CardHeader>
                <CardContent className="pt-0">
                  {data.top_reorder_recommendations.length === 0 ? (
                    <EmptyState
                      title="Everything looks healthy"
                      description="No urgent reorder actions right now."
                    />
                  ) : (
                    <div className="space-y-3">
                      {data.top_reorder_recommendations.map((rec) => (
                        <div
                          key={rec.product_id}
                          className="flex flex-col gap-3 rounded-md border border-border p-4 sm:flex-row sm:items-center sm:justify-between"
                        >
                          <div className="min-w-0 flex-1">
                            <div className="mb-1 flex items-center gap-2">
                              <RiskBadge risk={rec.risk} />
                              <p className="truncate font-medium text-foreground">{rec.product_name}</p>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {rec.days_until_stockout != null
                                ? `Stockout predicted in ${rec.days_until_stockout} day(s). `
                                : ""}
                              Current stock: {rec.current_stock} · 7-day forecast: {formatNumber(rec.forecast_7_days)}
                            </p>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <p className="text-xs text-muted-foreground">Recommended order</p>
                              <p className="text-lg font-semibold text-foreground">
                                {rec.recommended_order_quantity} units
                              </p>
                            </div>
                            <Link to={`/inventory/${rec.product_id}`}>
                              <Button size="sm" variant="outline">
                                View
                              </Button>
                            </Link>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Recent Alerts</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  {data.recent_alerts.length === 0 ? (
                    <EmptyState title="No alerts" description="Nothing needs your attention right now." />
                  ) : (
                    <div className="space-y-3">
                      {data.recent_alerts.map((alert) => (
                        <div key={alert.id} className="rounded-md border border-border p-3">
                          <p className="text-sm font-medium text-foreground">{alert.title}</p>
                          <p className="mt-0.5 text-xs text-muted-foreground">{alert.message}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  <Link to="/alerts">
                    <Button variant="ghost" size="sm" className="mt-2 w-full">
                      View all alerts <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Card>
                <CardContent className="p-5">
                  <p className="text-sm text-muted-foreground">Expected demand (next 7 days)</p>
                  <p className="mt-1 text-xl font-semibold text-foreground">
                    {formatNumber(data.expected_7_day_demand)} units
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-5">
                  <p className="text-sm text-muted-foreground">Capital locked in overstock</p>
                  <p className="mt-1 text-xl font-semibold text-foreground">
                    {formatCurrency(data.capital_locked)}
                  </p>
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>

      <GenerateDemoDialog open={demoOpen} onClose={() => setDemoOpen(false)} />
    </AppShell>
  );
}
