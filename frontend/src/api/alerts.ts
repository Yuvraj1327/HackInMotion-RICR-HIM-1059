import { apiClient } from "@/api/client";
import type { Alert } from "@/types/api";

export async function listAlerts(includeResolved = false): Promise<Alert[]> {
  const { data } = await apiClient.get<Alert[]>("/alerts", {
    params: { resolved: includeResolved },
  });
  return data;
}

export async function resolveAlert(alertId: string): Promise<Alert> {
  const { data } = await apiClient.post<Alert>(`/alerts/${alertId}/resolve`);
  return data;
}
