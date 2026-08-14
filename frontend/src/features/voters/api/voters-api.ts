import { apiClient } from "@/shared/lib/api-client";
import type {
  Voter,
  VoterCreateRequest,
  VoterListParams,
  VoterListResponse,
  VoterUpdateRequest,
} from "@/features/voters/api/types";

export async function listVoters(params: VoterListParams): Promise<VoterListResponse> {
  const response = await apiClient.get<VoterListResponse>("/voters", { params });
  return response.data;
}

export async function getVoter(id: string): Promise<Voter> {
  const response = await apiClient.get<Voter>(`/voters/${id}`);
  return response.data;
}

export async function createVoter(data: VoterCreateRequest): Promise<Voter> {
  const response = await apiClient.post<Voter>("/voters", data);
  return response.data;
}

export async function updateVoter(id: string, data: VoterUpdateRequest): Promise<Voter> {
  const response = await apiClient.patch<Voter>(`/voters/${id}`, data);
  return response.data;
}

export async function deleteVoter(id: string): Promise<void> {
  await apiClient.delete(`/voters/${id}`);
}
