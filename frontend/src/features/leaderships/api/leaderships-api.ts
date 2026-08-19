import { apiClient } from "@/shared/lib/api-client";
import type {
  Leadership,
  LeadershipCreateRequest,
  LeadershipListParams,
  LeadershipListResponse,
  LeadershipUpdateRequest,
} from "@/features/leaderships/api/types";

export async function listLeaderships(params: LeadershipListParams): Promise<LeadershipListResponse> {
  const response = await apiClient.get<LeadershipListResponse>("/leaderships", { params });
  return response.data;
}

export async function getLeadership(id: string): Promise<Leadership> {
  const response = await apiClient.get<Leadership>(`/leaderships/${id}`);
  return response.data;
}

export async function createLeadership(data: LeadershipCreateRequest): Promise<Leadership> {
  const response = await apiClient.post<Leadership>("/leaderships", data);
  return response.data;
}

export async function updateLeadership(id: string, data: LeadershipUpdateRequest): Promise<Leadership> {
  const response = await apiClient.patch<Leadership>(`/leaderships/${id}`, data);
  return response.data;
}

export async function deleteLeadership(id: string): Promise<void> {
  await apiClient.delete(`/leaderships/${id}`);
}

export async function getLeadershipVoterCounts(): Promise<Record<string, number>> {
  const response = await apiClient.get<{ counts: Record<string, number> }>("/leaderships/voter-counts");
  return response.data.counts;
}
