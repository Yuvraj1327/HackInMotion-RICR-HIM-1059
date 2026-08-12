import { AlertOctagon, AlertTriangle, CheckCircle2, PackageX } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import type { RiskLevel } from "@/types/api";

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  switch (risk) {
    case "CRITICAL":
      return (
        <Badge variant="critical">
          <AlertOctagon className="h-3 w-3" /> Critical
        </Badge>
      );
    case "HIGH":
      return (
        <Badge variant="critical">
          <AlertTriangle className="h-3 w-3" /> High Risk
        </Badge>
      );
    case "MEDIUM":
      return (
        <Badge variant="warning">
          <AlertTriangle className="h-3 w-3" /> Medium
        </Badge>
      );
    default:
      return (
        <Badge variant="success">
          <CheckCircle2 className="h-3 w-3" /> Low
        </Badge>
      );
  }
}

export type ProductStatus = "healthy" | "low_stock" | "critical" | "overstock";

/**
 * Combines the backend's own stockout-risk classification and
 * overstock flag into a single display status. No new business logic
 * is computed here — this only chooses which already-calculated
 * backend signal takes visual priority.
 */
export function deriveProductStatus(risk: RiskLevel | undefined, isOverstock: boolean | undefined): ProductStatus {
  if (isOverstock) return "overstock";
  if (risk === "CRITICAL" || risk === "HIGH") return "critical";
  if (risk === "MEDIUM") return "low_stock";
  return "healthy";
}

export function ProductStatusBadge({ status }: { status: ProductStatus }) {
  switch (status) {
    case "critical":
      return (
        <Badge variant="critical">
          <AlertOctagon className="h-3 w-3" /> Critical
        </Badge>
      );
    case "low_stock":
      return (
        <Badge variant="warning">
          <AlertTriangle className="h-3 w-3" /> Low Stock
        </Badge>
      );
    case "overstock":
      return (
        <Badge variant="overstock">
          <PackageX className="h-3 w-3" /> Overstock
        </Badge>
      );
    default:
      return (
        <Badge variant="success">
          <CheckCircle2 className="h-3 w-3" /> Healthy
        </Badge>
      );
  }
}
