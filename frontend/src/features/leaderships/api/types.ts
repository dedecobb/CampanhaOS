/**
 * Espelha src/presentation/api/v1/schemas/leaderships.py do backend.
 */

export const INFLUENCE_LEVEL_OPTIONS = [
  { value: "baixa", label: "Baixa" },
  { value: "media", label: "Média" },
  { value: "alta", label: "Alta" },
] as const;

export interface Leadership {
  id: string;
  created_by_user_id: string;
  name: string;
  region: string | null;
  estimated_votes: number;
  influence_level: string;
  team_size: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeadershipListResponse {
  items: Leadership[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface LeadershipFormValues {
  name: string;
  influence_level: string;
  region: string;
  estimated_votes: string; // input HTML é string; convertido para número antes de enviar
  team_size: string;
  notes: string;
}

export interface LeadershipCreateRequest {
  name: string;
  influence_level: string;
  region?: string | null;
  estimated_votes?: number;
  team_size?: number | null;
  notes?: string | null;
}

export type LeadershipUpdateRequest = Partial<LeadershipCreateRequest>;

export interface LeadershipListParams {
  search?: string;
  influence_level?: string;
  page?: number;
  page_size?: number;
}
