import { apiClient } from "@/api/client";
import type { OverstockAnalysis, StockoutPrediction } from "@/types/api";

export async function getStockoutPrediction(productId: string): Promise<StockoutPrediction> {
  const { data } = await apiClient.get<StockoutPrediction>(`/inventory/stockout/${productId}`);
  return data;
}

export async function listStockoutPredictions(): Promise<StockoutPrediction[]> {
  const { data } = await apiClient.get<StockoutPrediction[]>("/inventory/stockout");
  return data;
}

export async function getOverstockAnalysis(productId: string): Promise<OverstockAnalysis> {
  const { data } = await apiClient.get<OverstockAnalysis>(`/inventory/overstock/${productId}`);
  return data;
}

export async function listOverstockAnalyses(): Promise<OverstockAnalysis[]> {
  const { data } = await apiClient.get<OverstockAnalysis[]>("/inventory/overstock");
  return data;
}
