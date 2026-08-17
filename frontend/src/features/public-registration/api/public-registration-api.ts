import { apiClient } from "@/shared/lib/api-client";
import type {
  PublicCampaignInfo,
  PublicVoterRegistrationRequest,
  PublicVoterRegistrationResponse,
} from "@/features/public-registration/api/types";

export async function getCampaignInfo(token: string): Promise<PublicCampaignInfo> {
  const response = await apiClient.get<PublicCampaignInfo>(`/public/registration/${token}`);
  return response.data;
}

export async function submitPublicRegistration(
  token: string,
  data: PublicVoterRegistrationRequest,
): Promise<PublicVoterRegistrationResponse> {
  const response = await apiClient.post<PublicVoterRegistrationResponse>(`/public/registration/${token}`, data);
  return response.data;
}
