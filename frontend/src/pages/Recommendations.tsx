import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ShoppingCart, PartyPopper } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { RiskBadge } from "@/components/common/StatusBadges";
import { getReorderRecommendations } from "@/api/recommendations";
import { QUERY_KEYS } from "@/lib/constants";
import { formatNumber } from "@/lib/utils";
import { ApiError } from "@/api/client";

export default function Recommendations() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: QUERY_KEYS.recommendations,
    queryFn: () => getReorderRecommendations(50),
  });

  return (
    <AppShell title="Smart Reorder">
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Smart Reorder</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Prioritized reorder actions, ranked by urgency and computed from your live forecast and inventory data.
          </p>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-40 w-full" />
            ))}
          </div>
        ) : isError ? (
          <ErrorState message={error instanceof ApiError ? error.message : "Unable to load recommendations."} onRetry={() => refetch()} />
        ) : !data || data.length === 0 ? (
          <EmptyState
            icon={<PartyPopper className="h-9 w-9" />}
            title="Nothing to reorder right now"
            description="All products are within healthy stock levels."
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {data.map((rec) => (
              <Card key={rec.product_id} className="flex flex-col">
                <CardContent className="flex flex-1 flex-col gap-4 p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <RiskBadge risk={rec.risk} />
                      <h3 className="mt-2 text-base font-semibold text-foreground">{rec.product_name}</h3>
                    </div>
                    <ShoppingCart className="h-5 w-5 shrink-0 text-muted-foreground" />
                  </div>

                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div>
                      <p className="text-muted-foreground">Current stock</p>
                      <p className="font-semibold text-foreground">{rec.current_stock}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">7-day forecast</p>
                      <p className="font-semibold text-foreground">{formatNumber(rec.forecast_7_days)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Stockout</p>
                      <p className="font-semibold text-foreground">
                        {rec.days_until_stockout != null ? `${rec.days_until_stockout}d` : "—"}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-md bg-primary/[0.04] p-4">
                    <p className="text-xs text-muted-foreground">Recommended order</p>
                    <p className="text-2xl font-bold text-primary">{rec.recommended_order_quantity} units</p>
                  </div>

                  <p className="text-sm text-muted-foreground">{rec.reason}</p>

                  <div className="mt-auto">
                    <Link to={`/inventory/${rec.product_id}`}>
                      <Button variant="outline" size="sm" className="w-full">
                        View Product
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
