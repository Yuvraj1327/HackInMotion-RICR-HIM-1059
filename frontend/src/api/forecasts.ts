import { apiClient } from "@/api/client";
import type { ForecastGenerateResponse, ForecastRecord } from "@/types/api";

export async function generateForecast(
  productId: string,
  horizonDays: 7 | 14 | 30
): Promise<ForecastGenerateResponse> {
  const { data } = await apiClient.post<ForecastGenerateResponse>(
    `/forecasts/generate/${productId}`,
    { horizon_days: horizonDays }
  );
  return data;
}

export async function getForecastForProduct(productId: string): Promise<ForecastRecord[]> {
  const { data } = await apiClient.get<ForecastRecord[]>(`/forecasts/${productId}`);
  return data;
}

export async function listAllForecasts(): Promise<ForecastRecord[]> {
  const { data } = await apiClient.get<ForecastRecord[]>("/forecasts");
  return data;
}
