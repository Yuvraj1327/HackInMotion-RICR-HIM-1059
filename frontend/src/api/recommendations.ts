import { apiClient } from "@/api/client";
import type { ReorderRecommendation } from "@/types/api";

export async function getReorderRecommendations(limit = 20): Promise<ReorderRecommendation[]> {
  const { data } = await apiClient.get<ReorderRecommendation[]>("/recommendations/reorder", {
    params: { limit },
  });
  return data;
}
