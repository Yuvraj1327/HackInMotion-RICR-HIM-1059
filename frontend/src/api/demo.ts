import { apiClient } from "@/api/client";
import type { DemoSeedInput, DemoSeedResponse, MessageResponse } from "@/types/api";

export async function seedDemoData(input: DemoSeedInput): Promise<DemoSeedResponse> {
  const { data } = await apiClient.post<DemoSeedResponse>("/demo/seed", input);
  return data;
}

export async function resetDemoData(): Promise<MessageResponse> {
  const { data } = await apiClient.post<MessageResponse>("/demo/reset");
  return data;
}
