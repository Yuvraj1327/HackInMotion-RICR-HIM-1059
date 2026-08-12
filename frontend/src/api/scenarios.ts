import { apiClient } from "@/api/client";
import type { ScenarioSimulateInput, ScenarioSimulateResponse } from "@/types/api";

export async function simulateScenario(
  input: ScenarioSimulateInput
): Promise<ScenarioSimulateResponse> {
  const { data } = await apiClient.post<ScenarioSimulateResponse>("/scenarios/simulate", input);
  return data;
}
