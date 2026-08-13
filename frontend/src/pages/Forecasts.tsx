///forecaste.tsx

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LineChart as LineChartIcon, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { ForecastChart } from "@/components/forecasts/ForecastChart";
import { ForecastExplanationCard } from "@/components/forecasts/ForecastExplanationCard";
import { listProducts } from "@/api/products";
import { listSales } from "@/api/sales";
import { generateForecast } from "@/api/forecasts";
import { QUERY_KEYS, FORECAST_HORIZONS, type ForecastHorizon } from "@/lib/constants";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/api/client";
import type { ForecastGenerateResponse } from "@/types/api";

export default function Forecasts() {
  const [productId, setProductId] = useState<string>("");
  const [horizon, setHorizon] = useState<ForecastHorizon>(7);
  const [forecastResult, setForecastResult] = useState<ForecastGenerateResponse | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const productsQuery = useQuery({ queryKey: QUERY_KEYS.products, queryFn: () => listProducts({ limit: 500 }) });

  useEffect(() => {
    if (!productId && productsQuery.data && productsQuery.data.length > 0) {
      setProductId(productsQuery.data[0].id);
    }
  }, [productsQuery.data, productId]);

  const salesQuery = useQuery({
    queryKey: QUERY_KEYS.sales(productId),
    queryFn: () => listSales({ product_id: productId, limit: 500 }),
    enabled: !!productId,
  });

  const forecastMutation = useMutation({
    mutationFn: () => generateForecast(productId, horizon),
    onSuccess: (data) => {
      setForecastResult(data);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.forecasts(productId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard });
      toast({ variant: "success", title: "Forecast generated", description: `Model used: ${data.model}` });
    },
    onError: (err) => {
      toast({
        variant: "error",
        title: "Forecast could not be generated",
        description:
          err instanceof ApiError
            ? err.code === "insufficient_data"
              ? "Not enough historical sales data. Add more sales records or generate demo data."
              : err.message
            : undefined,
      });
    },
  });

  useEffect(() => {
    setForecastResult(null);
  }, [productId]);

  const selectedProduct = productsQuery.data?.find((p) => p.id === productId);

  return (
    <AppShell title="Demand Forecasting">
      <div className="space-y-6">
        <Card>
          <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex flex-1 flex-col gap-3 sm:flex-row sm:items-end">
              <div className="flex-1 sm:max-w-xs">
                <label className="mb-1.5 block text-sm font-medium text-foreground" htmlFor="forecast-product">
                  Product
                </label>
                <Select id="forecast-product" value={productId} onChange={(e) => setProductId(e.target.value)}>
                  {productsQuery.data?.length === 0 && <option value="">No products available</option>}
                  {productsQuery.data?.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.sku})
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-foreground">Horizon</label>
                <div className="flex rounded-md border border-border p-0.5">
                  {FORECAST_HORIZONS.map((h) => (
                    <button
                      key={h}
                      onClick={() => setHorizon(h)}
                      className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
                        horizon === h ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
                      }`}
                    >
                      {h} days
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <Button
              onClick={() => forecastMutation.mutate()}
              isLoading={forecastMutation.isPending}
              disabled={!productId}
            >
              <RefreshCw className="h-4 w-4" /> Generate Forecast
            </Button>
          </CardContent>
        </Card>

        {productsQuery.isLoading ? (
          <Skeleton className="h-96 w-full" />
        ) : productsQuery.isError ? (
          <ErrorState
            message={productsQuery.error instanceof ApiError ? productsQuery.error.message : "Unable to load products."}
            onRetry={() => productsQuery.refetch()}
          />
        ) : productsQuery.data?.length === 0 ? (
          <EmptyState
            icon={<LineChartIcon className="h-9 w-9" />}
            title="No products yet"
            description="Add a product or generate a demo store before forecasting demand."
          />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">{selectedProduct?.name ?? "Forecast"}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-0">
              {salesQuery.isLoading ? (
                <Skeleton className="h-80 w-full" />
              ) : salesQuery.data && salesQuery.data.length === 0 && !forecastResult ? (
                <EmptyState title="No sales history found" description="Upload a CSV or generate demo data to start forecasting." />
              ) : (
                <ForecastChart sales={salesQuery.data ?? []} forecastPoints={forecastResult?.forecast ?? []} />
              )}
              {forecastResult && <ForecastExplanationCard result={forecastResult} />}
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
