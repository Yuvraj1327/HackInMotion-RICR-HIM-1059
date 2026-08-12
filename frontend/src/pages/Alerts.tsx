import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, PartyPopper } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { listAlerts, resolveAlert } from "@/api/alerts";
import { listProducts } from "@/api/products";
import { QUERY_KEYS } from "@/lib/constants";
import { formatDateTime } from "@/lib/utils";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/api/client";
import type { Alert, AlertType, RiskLevel } from "@/types/api";

const SEVERITY_GROUP: Record<RiskLevel, "critical" | "warning" | "info"> = {
  CRITICAL: "critical",
  HIGH: "critical",
  MEDIUM: "warning",
  LOW: "info",
};

const SEVERITY_LABEL: Record<"critical" | "warning" | "info", string> = {
  critical: "🔴 Critical",
  warning: "🟠 Warning",
  info: "🟢 Information",
};

const ALERT_TYPE_LABELS: Record<AlertType, string> = {
  STOCKOUT: "Stockout",
  LOW_STOCK: "Low Stock",
  OVERSTOCK: "Overstock",
  DEMAND_SPIKE: "Demand Spike",
  DEMAND_DROP: "Demand Drop",
  DATA_ANOMALY: "Data Anomaly",
};

export default function Alerts() {
  const [typeFilter, setTypeFilter] = useState<AlertType | "all">("all");
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const alertsQuery = useQuery({ queryKey: QUERY_KEYS.alerts, queryFn: () => listAlerts(false) });
  const productsQuery = useQuery({ queryKey: QUERY_KEYS.products, queryFn: () => listProducts({ limit: 500 }) });
  const productNameMap = new Map(productsQuery.data?.map((p) => [p.id, p.name]));

  const resolveMutation = useMutation({
    mutationFn: (id: string) => resolveAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.alerts });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard });
      toast({ variant: "success", title: "Alert resolved" });
    },
    onError: (err) => {
      toast({ variant: "error", title: "Could not resolve alert", description: err instanceof ApiError ? err.message : undefined });
    },
  });

  const filtered = useMemo(() => {
    if (!alertsQuery.data) return [];
    if (typeFilter === "all") return alertsQuery.data;
    return alertsQuery.data.filter((a) => a.alert_type === typeFilter);
  }, [alertsQuery.data, typeFilter]);

  const grouped = useMemo(() => {
    const groups: Record<"critical" | "warning" | "info", Alert[]> = { critical: [], warning: [], info: [] };
    filtered.forEach((a) => groups[SEVERITY_GROUP[a.severity]].push(a));
    return groups;
  }, [filtered]);

  return (
    <AppShell title="Inventory Alerts">
      <div className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted-foreground">Alerts refresh automatically from your latest inventory data.</p>
          <Select
            className="sm:w-56"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as AlertType | "all")}
            aria-label="Filter by alert type"
          >
            <option value="all">All alert types</option>
            {Object.entries(ALERT_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </div>

        {alertsQuery.isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        ) : alertsQuery.isError ? (
          <ErrorState
            message={alertsQuery.error instanceof ApiError ? alertsQuery.error.message : "Unable to load alerts."}
            onRetry={() => alertsQuery.refetch()}
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<PartyPopper className="h-9 w-9" />}
            title="🎉 Everything looks healthy"
            description="No inventory risks detected."
          />
        ) : (
          (["critical", "warning", "info"] as const).map((group) =>
            grouped[group].length > 0 ? (
              <div key={group} className="space-y-3">
                <h2 className="text-sm font-semibold text-foreground">{SEVERITY_LABEL[group]}</h2>
                {grouped[group].map((alert) => (
                  <Card key={alert.id}>
                    <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="mb-1 flex flex-wrap items-center gap-2">
                          <Badge variant={group === "critical" ? "critical" : group === "warning" ? "warning" : "muted"}>
                            {ALERT_TYPE_LABELS[alert.alert_type]}
                          </Badge>
                          {alert.product_id && (
                            <span className="text-xs text-muted-foreground">
                              {productNameMap.get(alert.product_id) ?? alert.product_id}
                            </span>
                          )}
                        </div>
                        <p className="font-medium text-foreground">{alert.title}</p>
                        <p className="mt-0.5 text-sm text-muted-foreground">{alert.message}</p>
                        {alert.recommended_action && (
                          <p className="mt-1 text-sm text-primary">→ {alert.recommended_action}</p>
                        )}
                        <p className="mt-2 text-xs text-muted-foreground">{formatDateTime(alert.created_at)}</p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="shrink-0"
                        onClick={() => resolveMutation.mutate(alert.id)}
                        isLoading={resolveMutation.isPending && resolveMutation.variables === alert.id}
                      >
                        <CheckCircle2 className="h-4 w-4" /> Resolve
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : null
          )
        )}
      </div>
    </AppShell>
  );
}
