import { apiClient } from "@/shared/lib/api-client";
import type {
  FinanceAttachmentDownloadResponse,
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

export async function uploadFinanceAttachment(id: string, file: File): Promise<FinanceTransaction> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiClient.post<FinanceTransaction>(`/finance/${id}/attachment`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function removeFinanceAttachment(id: string): Promise<void> {
  await apiClient.delete(`/finance/${id}/attachment`);
}

export async function getFinanceAttachmentDownloadUrl(id: string): Promise<FinanceAttachmentDownloadResponse> {
  const response = await apiClient.get<FinanceAttachmentDownloadResponse>(`/finance/${id}/attachment/download-url`);
  return response.data;
}
