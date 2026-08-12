import { apiClient } from "@/api/client";
import type { DashboardSummary } from "@/types/api";

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await apiClient.get<DashboardSummary>("/dashboard/summary");
  return data;
}
