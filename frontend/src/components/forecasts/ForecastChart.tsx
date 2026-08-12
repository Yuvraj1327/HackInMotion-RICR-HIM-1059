import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatDate } from "@/lib/utils";
import type { ForecastPoint, Sale } from "@/types/api";

interface ChartRow {
  date: string;
  historical?: number;
  forecast?: number;
  lower?: number;
  upperBand?: number; // upper - lower, stacked on top of `lower` to render the shaded band
}

function buildChartData(sales: Sale[], forecastPoints: ForecastPoint[]): ChartRow[] {
  // Aggregate raw sales transactions into a daily total for the "Historical
  // Demand" line - this is a display-only grouping, not a forecasting
  // calculation (the backend already computes its own zero-filled daily
  // series internally for modeling).
  const byDate = new Map<string, number>();
  sales.forEach((s) => {
    const day = s.sale_date.slice(0, 10);
    byDate.set(day, (byDate.get(day) ?? 0) + s.quantity);
  });

  const historicalRows: ChartRow[] = Array.from(byDate.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-30) // last 30 days of history keeps the chart readable
    .map(([date, historical]) => ({ date, historical }));

  const forecastRows: ChartRow[] = forecastPoints.map((p) => ({
    date: p.date,
    forecast: p.predicted_demand,
    lower: p.lower_bound,
    upperBand: Math.max(0, p.upper_bound - p.lower_bound),
  }));

  return [...historicalRows, ...forecastRows];
}

export function ForecastChart({ sales, forecastPoints }: { sales: Sale[]; forecastPoints: ForecastPoint[] }) {
  const data = buildChartData(sales, forecastPoints);
  const hasRange = forecastPoints.length > 0;

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          dataKey="date"
          tickFormatter={(v) => formatDate(v)}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          minTickGap={24}
        />
        <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} width={36} />
        <Tooltip
          labelFormatter={(v) => formatDate(v as string)}
          contentStyle={{
            borderRadius: 8,
            border: "1px solid hsl(var(--border))",
            fontSize: 12,
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {hasRange && (
          <>
            <Area
              dataKey="lower"
              stackId="range"
              stroke="none"
              fill="transparent"
              legendType="none"
              isAnimationActive={false}
            />
            <Area
              dataKey="upperBand"
              stackId="range"
              stroke="none"
              fill="hsl(var(--primary))"
              fillOpacity={0.08}
              name="Forecast range"
              isAnimationActive={false}
            />
          </>
        )}
        <Line
          type="monotone"
          dataKey="historical"
          name="Historical Demand"
          stroke="hsl(var(--foreground))"
          strokeWidth={2}
          dot={false}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="forecast"
          name="Forecast"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          strokeDasharray="6 4"
          dot={false}
          connectNulls
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
