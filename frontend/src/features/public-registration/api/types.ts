export const GENDER_OPTIONS = [
  { value: "feminino", label: "Feminino" },
  { value: "masculino", label: "Masculino" },
  { value: "nao_binario", label: "Não-binário" },
  { value: "prefere_nao_informar", label: "Prefere não informar" },
  { value: "outro", label: "Outro" },
] as const;

export interface PublicCampaignInfo {
  tenant_name: string;
}

export interface PublicVoterRegistrationRequest {
  name: string;
  consent_given: boolean;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  neighborhood?: string | null;
  gender?: string | null;
  birth_date?: string | null;
}

export interface PublicVoterRegistrationResponse {
  success: boolean;
  message: string;
}
