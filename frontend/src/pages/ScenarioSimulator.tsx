import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { FlaskConical, TrendingUp, Truck } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { RiskBadge } from "@/components/common/StatusBadges";
import { listProducts } from "@/api/products";
import { simulateScenario } from "@/api/scenarios";
import { QUERY_KEYS } from "@/lib/constants";
import { formatDate, formatNumber } from "@/lib/utils";
import { ApiError } from "@/api/client";

export default function ScenarioSimulator() {
  const [productId, setProductId] = useState("");
  const [demandChange, setDemandChange] = useState(0);
  const [supplierDelay, setSupplierDelay] = useState(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const productsQuery = useQuery({ queryKey: QUERY_KEYS.products, queryFn: () => listProducts({ limit: 500 }) });

  useEffect(() => {
    if (!productId && productsQuery.data && productsQuery.data.length > 0) {
      setProductId(productsQuery.data[0].id);
    }
  }, [productsQuery.data, productId]);

  const mutation = useMutation({
    mutationFn: () => simulateScenario({ product_id: productId, demand_change_percent: demandChange, supplier_delay_days: supplierDelay }),
  });

  // Debounce API calls as sliders move, so we don't fire a request per pixel of drag.
  useEffect(() => {
    if (!productId) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      mutation.mutate();
    }, 400);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId, demandChange, supplierDelay]);

  return (
    <AppShell title="Scenario Simulator">
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Scenario Simulator</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Model how a demand shift or a supplier delay would affect stockout risk and reorder quantities.
          </p>
        </div>

        {productsQuery.isLoading ? (
          <Skeleton className="h-72 w-full" />
        ) : productsQuery.isError ? (
          <ErrorState
            message={productsQuery.error instanceof ApiError ? productsQuery.error.message : "Unable to load products."}
            onRetry={() => productsQuery.refetch()}
          />
        ) : productsQuery.data?.length === 0 ? (
          <EmptyState icon={<FlaskConical className="h-9 w-9" />} title="No products yet" description="Add a product before running scenarios." />
        ) : (
          <>
            <Card>
              <CardContent className="space-y-6 p-5">
                <div className="max-w-xs">
                  <label className="mb-1.5 block text-sm font-medium text-foreground" htmlFor="scenario-product">
                    Product
                  </label>
                  <Select id="scenario-product" value={productId} onChange={(e) => setProductId(e.target.value)}>
                    {productsQuery.data?.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.sku})
                      </option>
                    ))}
                  </Select>
                </div>

                <div>
                  <div className="mb-1.5 flex items-center justify-between">
                    <label className="flex items-center gap-1.5 text-sm font-medium text-foreground" htmlFor="demand-slider">
                      <TrendingUp className="h-4 w-4" /> Demand Change
                    </label>
                    <span className="text-sm font-semibold text-primary">
                      {demandChange > 0 ? "+" : ""}
                      {demandChange}%
                    </span>
                  </div>
                  <input
                    id="demand-slider"
                    type="range"
                    min={-20}
                    max={50}
                    step={5}
                    value={demandChange}
                    onChange={(e) => setDemandChange(Number(e.target.value))}
                    className="w-full accent-[hsl(var(--primary))]"
                  />
                  <div className="mt-1 flex justify-between text-xs text-muted-foreground">
                    <span>-20%</span>
                    <span>+50%</span>
                  </div>
                </div>

                <div>
                  <div className="mb-1.5 flex items-center justify-between">
                    <label className="flex items-center gap-1.5 text-sm font-medium text-foreground" htmlFor="delay-slider">
                      <Truck className="h-4 w-4" /> Supplier Delay
                    </label>
                    <span className="text-sm font-semibold text-primary">{supplierDelay} days</span>
                  </div>
                  <input
                    id="delay-slider"
                    type="range"
                    min={0}
                    max={10}
                    step={1}
                    value={supplierDelay}
                    onChange={(e) => setSupplierDelay(Number(e.target.value))}
                    className="w-full accent-[hsl(var(--primary))]"
                  />
                  <div className="mt-1 flex justify-between text-xs text-muted-foreground">
                    <span>0 days</span>
                    <span>10 days</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {mutation.isPending && !mutation.data ? (
              <Skeleton className="h-56 w-full" />
            ) : mutation.isError ? (
              <ErrorState
                message={mutation.error instanceof ApiError ? mutation.error.message : "Unable to run scenario."}
                onRetry={() => mutation.mutate()}
              />
            ) : mutation.data ? (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Current Scenario</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 pt-0">
                    <ScenarioRow label="7-day forecast" value={`${formatNumber(mutation.data.baseline_demand_7d)} units`} />
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Risk</span>
                      <RiskBadge risk={mutation.data.baseline_risk} />
                    </div>
                    <ScenarioRow label="Stockout date" value={formatDate(mutation.data.baseline_stockout_date)} />
                    <ScenarioRow
                      label="Days until stockout"
                      value={mutation.data.baseline_days_until_stockout != null ? `${mutation.data.baseline_days_until_stockout} days` : "—"}
                    />
                    <ScenarioRow label="Recommended order" value={`${mutation.data.baseline_recommended_order_quantity} units`} />
                  </CardContent>
                </Card>

                <Card className="border-primary/30">
                  <CardHeader>
                    <CardTitle className="text-base">New Scenario</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 pt-0">
                    <ScenarioRow label="7-day forecast" value={`${formatNumber(mutation.data.scenario_demand_7d)} units`} highlight />
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Risk</span>
                      <RiskBadge risk={mutation.data.scenario_risk} />
                    </div>
                    <ScenarioRow label="Stockout date" value={formatDate(mutation.data.scenario_stockout_date)} highlight />
                    <ScenarioRow
                      label="Days until stockout"
                      value={mutation.data.scenario_days_until_stockout != null ? `${mutation.data.scenario_days_until_stockout} days` : "—"}
                      highlight
                    />
                    <ScenarioRow label="Recommended order" value={`${mutation.data.scenario_recommended_order_quantity} units`} highlight />
                    <div className="mt-2 rounded-md bg-primary/[0.06] p-3">
                      <p className="text-xs text-muted-foreground">Additional inventory needed</p>
                      <p className="text-xl font-bold text-primary">{mutation.data.additional_units_required} units</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : null}
          </>
        )}
      </div>
    </AppShell>
  );
}

function ScenarioRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className={`font-semibold ${highlight ? "text-primary" : "text-foreground"}`}>{value}</span>
    </div>
  );
}
