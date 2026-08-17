export interface RegistrationGrowthPoint {
  day: string;
  count: number;
}

export interface DashboardStats {
  total_voters: number;
  voter_goal: number | null;
  gender_breakdown: Record<string, number>;
  age_breakdown: Record<string, number>;
  registration_growth: RegistrationGrowthPoint[];
  self_registered_count: number;
  staff_registered_count: number;
}

/** Ordem fixa das faixas etárias — o backend não garante essa ordem (vem de GROUP BY). */
export const AGE_BRACKET_ORDER = ["16-17", "18-24", "25-34", "35-44", "45-59", "60+", "nao_informado"];

export const AGE_BRACKET_LABELS: Record<string, string> = {
  "16-17": "16-17",
  "18-24": "18-24",
  "25-34": "25-34",
  "35-44": "35-44",
  "45-59": "45-59",
  "60+": "60+",
  nao_informado: "Não informado",
};

export const GENDER_LABELS: Record<string, string> = {
  feminino: "Feminino",
  masculino: "Masculino",
  nao_binario: "Não-binário",
  prefere_nao_informar: "Prefere não informar",
  outro: "Outro",
  nao_informado: "Não informado",
};

// Azul para masculino, rosa para feminino (convenção que o usuário pediu),
// cores distintas pras demais categorias — nenhuma fica "escondida".
export const GENDER_COLORS: Record<string, string> = {
  feminino: "#ec4899",
  masculino: "#3b82f6",
  nao_binario: "#a855f7",
  prefere_nao_informar: "#9ca3af",
  outro: "#14b8a6",
  nao_informado: "#9ca3af",
};
