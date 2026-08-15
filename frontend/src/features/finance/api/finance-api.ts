import { apiClient } from "@/shared/lib/api-client";
import type {
  FinanceTransaction,
  FinanceTransactionCreateRequest,
  FinanceTransactionListParams,
  FinanceTransactionListResponse,
  FinanceTransactionUpdateRequest,
} from "@/features/finance/api/types";

export async function listFinanceTransactions(
  params: FinanceTransactionListParams,
): Promise<FinanceTransactionListResponse> {
  const response = await apiClient.get<FinanceTransactionListResponse>("/finance", { params });
  return response.data;
}

export async function getFinanceTransaction(id: string): Promise<FinanceTransaction> {
  const response = await apiClient.get<FinanceTransaction>(`/finance/${id}`);
  return response.data;
}

export async function createFinanceTransaction(data: FinanceTransactionCreateRequest): Promise<FinanceTransaction> {
  const response = await apiClient.post<FinanceTransaction>("/finance", data);
  return response.data;
}

export async function updateFinanceTransaction(
  id: string,
  data: FinanceTransactionUpdateRequest,
): Promise<FinanceTransaction> {
  const response = await apiClient.patch<FinanceTransaction>(`/finance/${id}`, data);
  return response.data;
}

export async function deleteFinanceTransaction(id: string): Promise<void> {
  await apiClient.delete(`/finance/${id}`);
}
