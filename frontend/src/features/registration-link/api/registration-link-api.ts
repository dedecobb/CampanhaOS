import { apiClient } from "@/shared/lib/api-client";
import type { RegistrationTokenResponse } from "@/features/registration-link/api/types";

export async function getRegistrationLink(): Promise<RegistrationTokenResponse> {
  const response = await apiClient.get<RegistrationTokenResponse>("/tenant/registration-link");
  return response.data;
}

export async function generateRegistrationLink(): Promise<RegistrationTokenResponse> {
  const response = await apiClient.post<RegistrationTokenResponse>("/tenant/registration-link");
  return response.data;
}

export async function revokeRegistrationLink(): Promise<void> {
  await apiClient.delete("/tenant/registration-link");
}
