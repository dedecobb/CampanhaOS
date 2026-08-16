/**
 * Espelha src/presentation/api/v1/schemas/voters.py do backend.
 *
 * Nota de escopo: o frontend (Bloco D) só expõe os campos mais usados no
 * dia a dia. `latitude`/`longitude`/`custom_fields`/`leadership_id`
 * existem na API e no tipo abaixo (para não perder o dado ao editar um
 * registro que já os tenha), mas não têm campo de formulário ainda.
 */

export const LEGAL_BASIS_OPTIONS = [
  { value: "consentimento", label: "Consentimento" },
  { value: "obrigacao_legal", label: "Obrigação legal" },
  { value: "execucao_de_contrato", label: "Execução de contrato" },
  { value: "interesse_legitimo", label: "Interesse legítimo" },
  { value: "protecao_da_vida", label: "Proteção da vida" },
  { value: "exercicio_regular_de_direitos", label: "Exercício regular de direitos" },
] as const;

export interface Voter {
  id: string;
  created_by_user_id: string;
  name: string;
  phone: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  neighborhood: string | null;
  latitude: number | null;
  longitude: number | null;
  tags: string[];
  custom_fields: Record<string, string>;
  notes: string | null;
  legal_basis: string;
  created_at: string;
  updated_at: string;
  leadership_id: string | null;
}

export interface VoterListResponse {
  items: Voter[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface VoterFormValues {
  name: string;
  legal_basis: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  postal_code: string;
  neighborhood: string;
  latitude: number | null;
  longitude: number | null;
  /**
   * true só quando o usuário arrastou/clicou no mapa NESTA sessão de
   * edição — distingue "coordenada que já existia" (não deve impedir
   * re-geocodificação automática se o endereço mudar) de "ajuste manual
   * de verdade" (deve ser respeitado, nunca sobrescrito).
   */
  locationManuallyAdjusted: boolean;
  tags: string; // no formulário, tags é uma string separada por vírgula — convertida para array antes de enviar
  notes: string;
}

export interface VoterCreateRequest {
  name: string;
  legal_basis: string;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  neighborhood?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  tags?: string[];
  notes?: string | null;
}

export type VoterUpdateRequest = Partial<VoterCreateRequest>;

export interface VoterListParams {
  search?: string;
  tags?: string[];
  page?: number;
  page_size?: number;
}
