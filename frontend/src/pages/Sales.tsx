///sales.tsx




import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Rocket, Receipt } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { CsvUploadCard } from "@/components/common/CsvUploadCard";
import { GenerateDemoDialog } from "@/components/dashboard/GenerateDemoDialog";
import { listSales } from "@/api/sales";
import { listProducts } from "@/api/products";
import { QUERY_KEYS } from "@/lib/constants";
import { formatCurrencyFull, formatDate } from "@/lib/utils";
import { ApiError } from "@/api/client";

export default function Sales() {
  const [demoOpen, setDemoOpen] = useState(false);

  const salesQuery = useQuery({
    queryKey: QUERY_KEYS.sales(),
    queryFn: () => listSales({ limit: 50 }),
  });
  const productsQuery = useQuery({ queryKey: QUERY_KEYS.products, queryFn: () => listProducts({ limit: 500 }) });

  const productNameMap = new Map(productsQuery.data?.map((p) => [p.id, p.name]));

  return (
    <AppShell title="Sales Data">
      <div className="space-y-6">
        <Card className="border-primary/20 bg-primary/[0.03]">
          <CardContent className="flex flex-col items-center gap-3 p-6 text-center sm:flex-row sm:justify-between sm:text-left">
            <div>
              <h2 className="text-base font-semibold text-foreground">🚀 Don't have sales data handy?</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Generate a realistic demo store with products and sales history in seconds.
              </p>
            </div>
            <Button onClick={() => setDemoOpen(true)} className="shrink-0">
              <Rocket className="h-4 w-4" /> Generate Demo Store
            </Button>
          </CardContent>
        </Card>

        <CsvUploadCard />

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Sales</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {salesQuery.isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-8 w-full" />
                ))}
              </div>
            ) : salesQuery.isError ? (
              <ErrorState
                message={salesQuery.error instanceof ApiError ? salesQuery.error.message : "Unable to load sales."}
                onRetry={() => salesQuery.refetch()}
              />
            ) : !salesQuery.data || salesQuery.data.length === 0 ? (
              <EmptyState
                icon={<Receipt className="h-9 w-9" />}
                title="No sales history found"
                description="Upload a CSV or generate demo data to start forecasting."
              />
            ) : (
              <div className="overflow-x-auto scrollbar-thin">
                <table className="w-full min-w-[600px] text-sm">
                  <thead className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">Date</th>
                      <th className="px-3 py-2 font-medium">Product</th>
                      <th className="px-3 py-2 font-medium">Quantity</th>
                      <th className="px-3 py-2 font-medium">Unit Price</th>
                      <th className="px-3 py-2 font-medium">Promotion</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {salesQuery.data.map((sale) => (
                      <tr key={sale.id}>
                        <td className="px-3 py-2 text-muted-foreground">{formatDate(sale.sale_date)}</td>
                        <td className="px-3 py-2 text-foreground">
                          {productNameMap.get(sale.product_id) ?? sale.product_id}
                        </td>
                        <td className="px-3 py-2 text-foreground">{sale.quantity}</td>
                        <td className="px-3 py-2 text-foreground">{formatCurrencyFull(sale.unit_price)}</td>
                        <td className="px-3 py-2 text-muted-foreground">{sale.promotion ? "Yes" : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <GenerateDemoDialog open={demoOpen} onClose={() => setDemoOpen(false)} />
    </AppShell>
  );
}
