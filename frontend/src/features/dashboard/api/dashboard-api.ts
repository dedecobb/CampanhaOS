import { apiClient } from "@/shared/lib/api-client";
import type { DashboardStats } from "@/features/dashboard/api/types";

export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await apiClient.get<DashboardStats>("/dashboard/stats");
  return response.data;
}

export async function setVoterGoal(goal: number): Promise<DashboardStats> {
  const response = await apiClient.put<DashboardStats>("/dashboard/voter-goal", { goal });
  return response.data;
}

export async function clearVoterGoal(): Promise<void> {
  await apiClient.delete("/dashboard/voter-goal");
}
