/**
 * Espelha src/presentation/api/v1/schemas/auth.py do backend.
 */

export interface LoginRequest {
  tenant_id: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface UserMeResponse {
  id: string;
  tenant_id: string;
  name: string;
  email: string;
  role_names: string[];
}
