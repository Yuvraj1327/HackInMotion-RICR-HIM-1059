import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Pencil, Trash2, RefreshCw, PackageSearch } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { RiskBadge } from "@/components/common/StatusBadges";
import { ForecastChart } from "@/components/forecasts/ForecastChart";
import { ForecastExplanationCard } from "@/components/forecasts/ForecastExplanationCard";
import { ProductFormModal } from "@/components/inventory/ProductFormModal";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { getProduct, deleteProduct } from "@/api/products";
import { getStockoutPrediction } from "@/api/inventory";
import { listSales } from "@/api/sales";
import { generateForecast } from "@/api/forecasts";
import { getReorderRecommendations } from "@/api/recommendations";
import { getSupplier } from "@/api/suppliers";
import { QUERY_KEYS, FORECAST_HORIZONS, type ForecastHorizon } from "@/lib/constants";
import { formatCurrencyFull, formatDate, formatNumber } from "@/lib/utils";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/api/client";
import type { ForecastGenerateResponse } from "@/types/api";

export default function ProductDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [horizon, setHorizon] = useState<ForecastHorizon>(7);
  const [forecastResult, setForecastResult] = useState<ForecastGenerateResponse | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const productQuery = useQuery({
    queryKey: QUERY_KEYS.product(id!),
    queryFn: () => getProduct(id!),
    enabled: !!id,
  });

  const supplierQuery = useQuery({
    queryKey: ["suppliers", productQuery.data?.supplier_id],
    queryFn: () => getSupplier(productQuery.data!.supplier_id as string),
    enabled: !!productQuery.data?.supplier_id,
  });

  const stockoutQuery = useQuery({
    queryKey: QUERY_KEYS.stockout(id),
    queryFn: () => getStockoutPrediction(id!),
    enabled: !!id,
  });

  const salesQuery = useQuery({
    queryKey: QUERY_KEYS.sales(id),
    queryFn: () => listSales({ product_id: id, limit: 500 }),
    enabled: !!id,
  });

  const recommendationsQuery = useQuery({
    queryKey: QUERY_KEYS.recommendations,
    queryFn: () => getReorderRecommendations(200),
  });
  const recommendation = recommendationsQuery.data?.find((r) => r.product_id === id);

  const forecastMutation = useMutation({
    mutationFn: () => generateForecast(id!, horizon),
    onSuccess: (data) => {
      setForecastResult(data);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.forecasts(id) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard });
    },
    onError: (err) => {
      toast({
        variant: "error",
        title: "Could not generate forecast",
        description:
          err instanceof ApiError
            ? err.code === "insufficient_data"
              ? "Not enough historical sales data. Add more sales records or generate demo data."
              : err.message
            : undefined,
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteProduct(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.products });
      toast({ variant: "success", title: "Product deleted" });
      navigate("/inventory");
    },
    onError: (err) => {
      toast({ variant: "error", title: "Could not delete", description: err instanceof ApiError ? err.message : undefined });
    },
  });

  if (productQuery.isLoading) {
    return (
      <AppShell title="Product">
        <Skeleton className="h-64 w-full" />
      </AppShell>
    );
  }

  if (productQuery.isError || !productQuery.data) {
    return (
      <AppShell title="Product">
        <ErrorState
          message={productQuery.error instanceof ApiError ? productQuery.error.message : "Product not found."}
          onRetry={() => productQuery.refetch()}
        />
      </AppShell>
    );
  }

  const product = productQuery.data;
  const stockout = stockoutQuery.data;

  return (
    <AppShell title="Product Details">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Link to="/inventory" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> Back to Inventory
          </Link>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}>
              <Pencil className="h-4 w-4" /> Edit
            </Button>
            <Button variant="outline" size="sm" onClick={() => setDeleteOpen(true)}>
              <Trash2 className="h-4 w-4 text-critical" /> Delete
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Product Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 pt-0 text-sm">
              <Row label="Name" value={product.name} />
              <Row label="SKU" value={product.sku} />
              <Row label="Category" value={product.category} />
              <Row label="Price" value={formatCurrencyFull(product.price)} />
              <Row label="Cost" value={formatCurrencyFull(product.cost_price)} />
              <Row label="Supplier" value={supplierQuery.data?.name ?? "—"} />
              <Row label="Lead time" value={`${product.lead_time_days} days`} />
              <Row label="Current stock" value={`${product.current_stock} ${product.unit}`} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Inventory Health</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 pt-0 text-sm">
              {stockoutQuery.isLoading ? (
                <Skeleton className="h-32 w-full" />
              ) : stockout ? (
                <>
                  <Row label="Current stock" value={String(stockout.current_stock)} />
                  <Row label="Avg. daily demand" value={formatNumber(stockout.average_daily_demand)} />
                  <Row
                    label="Days of inventory"
                    value={stockout.days_of_inventory != null ? `${stockout.days_of_inventory} days` : "—"}
                  />
                  <Row label="Reorder point" value={formatNumber(stockout.reorder_point)} />
                  <Row label="Safety stock" value={formatNumber(stockout.safety_stock)} />
                </>
              ) : (
                <p className="text-muted-foreground">Unable to load inventory health.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Stockout Prediction</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-0 text-sm">
              {stockoutQuery.isLoading ? (
                <Skeleton className="h-32 w-full" />
              ) : stockout ? (
                <>
                  <RiskBadge risk={stockout.stockout_risk} />
                  <Row label="Expected stockout" value={formatDate(stockout.estimated_stockout_date)} />
                  <Row
                    label="Days remaining"
                    value={stockout.days_until_stockout != null ? `${stockout.days_until_stockout} days` : "—"}
                  />
                </>
              ) : (
                <p className="text-muted-foreground">Unable to load stockout prediction.</p>
              )}
            </CardContent>
          </Card>
        </div>

        {recommendation && (
          <Card className="border-primary/20 bg-primary/[0.03]">
            <CardContent className="p-5">
              <p className="text-sm font-medium text-muted-foreground">Recommendation</p>
              <p className="mt-1 text-2xl font-semibold text-foreground">
                Order {recommendation.recommended_order_quantity} units
              </p>
              <p className="mt-1 text-sm text-muted-foreground">{recommendation.reason}</p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader className="flex-row items-center justify-between flex-wrap gap-3">
            <CardTitle className="text-base">Demand Forecast</CardTitle>
            <div className="flex items-center gap-2">
              <div className="flex rounded-md border border-border p-0.5">
                {FORECAST_HORIZONS.map((h) => (
                  <button
                    key={h}
                    onClick={() => setHorizon(h)}
                    className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                      horizon === h ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
                    }`}
                  >
                    {h}d
                  </button>
                ))}
              </div>
              <Button size="sm" onClick={() => forecastMutation.mutate()} isLoading={forecastMutation.isPending}>
                <RefreshCw className="h-3.5 w-3.5" /> Generate Forecast
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-0">
            {salesQuery.isLoading ? (
              <Skeleton className="h-80 w-full" />
            ) : salesQuery.data && salesQuery.data.length === 0 && !forecastResult ? (
              <EmptyState
                icon={<PackageSearch className="h-9 w-9" />}
                title="No sales history found"
                description="Upload a CSV or generate demo data to start forecasting."
              />
            ) : (
              <ForecastChart sales={salesQuery.data ?? []} forecastPoints={forecastResult?.forecast ?? []} />
            )}
            {forecastResult && <ForecastExplanationCard result={forecastResult} />}
          </CardContent>
        </Card>
      </div>

      <ProductFormModal open={editOpen} onClose={() => setEditOpen(false)} product={product} />
      <ConfirmDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete product"
        description={`Are you sure you want to delete "${product.name}"? This cannot be undone.`}
        isLoading={deleteMutation.isPending}
      />
    </AppShell>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-foreground">{value}</span>
    </div>
  );
}
