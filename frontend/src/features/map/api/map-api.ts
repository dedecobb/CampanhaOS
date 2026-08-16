import { apiClient } from "@/shared/lib/api-client";
import type { VoterMapPoint } from "@/features/map/api/types";

export async function listVoterMapPoints(): Promise<VoterMapPoint[]> {
  const response = await apiClient.get<VoterMapPoint[]>("/voters/map");
  return response.data;
}
