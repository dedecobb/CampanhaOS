/**
 * Espelha src/presentation/api/v1/schemas/finance.py do backend.
 *
 * IMPORTANTE: `amount` e os campos do resumo vêm como STRING, não
 * number — confirmado pelos testes reais do backend
 * (`assert transaction["amount"] == "1000.00"`, Módulo 6). O Pydantic
 * serializa `Decimal` como string no JSON pra preservar precisão exata
 * — é o mesmo motivo pelo qual usamos Decimal no backend em vez de
 * float (Bloco A do Módulo 6). O frontend NUNCA deve fazer conta com
 * esses valores como número JavaScript (que voltaria a ter o problema
 * de arredondamento que o backend evitou) — só exibe como texto.
 */

export const TRANSACTION_TYPE_OPTIONS = [
  { value: "receita", label: "Receita" },
  { value: "despesa", label: "Despesa" },
  { value: "doacao", label: "Doação" },
] as const;

export interface FinanceTransaction {
  id: string;
  created_by_user_id: string;
  type: string;
  category: string;
  amount: string;
  description: string | null;
  occurred_at: string;
  created_at: string;
  updated_at: string;
}

export interface FinanceSummary {
  total_receitas: string;
  total_despesas: string;
  total_doacoes: string;
  saldo: string;
}

export interface FinanceTransactionListResponse {
  items: FinanceTransaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  summary: FinanceSummary;
}

export interface FinanceTransactionFormValues {
  type: string;
  category: string;
  amount: string;
  occurred_at: string;
  description: string;
}

export interface FinanceTransactionCreateRequest {
  type: string;
  category: string;
  amount: string;
  occurred_at: string;
  description?: string | null;
}

export type FinanceTransactionUpdateRequest = Partial<FinanceTransactionCreateRequest>;

export interface FinanceTransactionListParams {
  type?: string;
  category?: string;
  occurred_after?: string;
  occurred_before?: string;
  page?: number;
  page_size?: number;
}

/** Formata um valor Decimal-como-string para exibição em R$, sem passar por número JS. */
export function formatCurrencyFromString(value: string): string {
  const isNegative = value.startsWith("-");
  const unsigned = isNegative ? value.slice(1) : value;
  const [integerPart, decimalPart = "00"] = unsigned.split(".");
  const withThousands = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${isNegative ? "-" : ""}R$ ${withThousands},${decimalPart}`;
}
