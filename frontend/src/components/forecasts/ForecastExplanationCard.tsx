import { Lightbulb } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type { ForecastGenerateResponse } from "@/types/api";

/**
 * Builds a plain-language explanation strictly from fields the backend
 * actually returned (model name, notes, metrics) - never invents facts
 * the API didn't provide.
 */
function buildExplanation(result: ForecastGenerateResponse): string {
  const parts: string[] = [];

  if (result.notes) {
    parts.push(result.notes);
  } else {
    parts.push(
      `This forecast was produced using ${result.model} based on ${result.training_records} day(s) of historical sales.`
    );
  }

  if (result.metrics.mape != null) {
    parts.push(
      `On held-out validation data, the model's predictions were off by an average of ${result.metrics.mape.toFixed(1)}% (MAPE).`
    );
  }

  return parts.join(" ");
}

export function ForecastExplanationCard({ result }: { result: ForecastGenerateResponse }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2">
        <Lightbulb className="h-4 w-4 text-primary" />
        <CardTitle className="text-base">Why this forecast?</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        <p className="text-sm text-muted-foreground">{buildExplanation(result)}</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Metric label="Model" value={result.model} />
          <Metric label="Confidence" value={`${Math.round(result.confidence * 100)}%`} />
          <Metric label="MAPE" value={result.metrics.mape != null ? `${result.metrics.mape.toFixed(1)}%` : "—"} />
          <Metric label="RMSE" value={result.metrics.rmse != null ? result.metrics.rmse.toFixed(2) : "—"} />
        </div>
      </CardContent>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted/60 px-3 py-2">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-0.5 truncate text-sm font-semibold text-foreground">{value}</p>
    </div>
  );
}
