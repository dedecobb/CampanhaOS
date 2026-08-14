import { apiClient } from "@/shared/lib/api-client";
import type { LoginRequest, RefreshTokenRequest, TokenResponse, UserMeResponse } from "@/features/auth/api/types";

export async function login(request: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", request);
  return response.data;
}

export async function refreshToken(request: RefreshTokenRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/refresh", request);
  return response.data;
}

export async function getCurrentUser(): Promise<UserMeResponse> {
  const response = await apiClient.get<UserMeResponse>("/auth/me");
  return response.data;
}
