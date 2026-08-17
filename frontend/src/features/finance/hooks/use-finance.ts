import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createFinanceTransaction,
  deleteFinanceTransaction,
  getFinanceAttachmentDownloadUrl,
  getFinanceTransaction,
  listFinanceTransactions,
  removeFinanceAttachment,
  updateFinanceTransaction,
  uploadFinanceAttachment,
} from "@/features/finance/api/finance-api";
import type {
  FinanceTransactionCreateRequest,
  FinanceTransactionListParams,
  FinanceTransactionUpdateRequest,
} from "@/features/finance/api/types";

const FINANCE_QUERY_KEY = "finance";

export function useFinanceTransactions(params: FinanceTransactionListParams) {
  return useQuery({
    queryKey: [FINANCE_QUERY_KEY, params],
    queryFn: () => listFinanceTransactions(params),
  });
}

export function useFinanceTransaction(id: string | undefined) {
  return useQuery({
    queryKey: [FINANCE_QUERY_KEY, id],
    queryFn: () => getFinanceTransaction(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateFinanceTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: FinanceTransactionCreateRequest) => createFinanceTransaction(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [FINANCE_QUERY_KEY] });
    },
  });
}

export function useUpdateFinanceTransaction(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: FinanceTransactionUpdateRequest) => updateFinanceTransaction(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [FINANCE_QUERY_KEY] });
    },
  });
}

export function useDeleteFinanceTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteFinanceTransaction(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [FINANCE_QUERY_KEY] });
    },
  });
}

export function useUploadFinanceAttachment(transactionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadFinanceAttachment(transactionId, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [FINANCE_QUERY_KEY] });
    },
  });
}

export function useRemoveFinanceAttachment(transactionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => removeFinanceAttachment(transactionId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [FINANCE_QUERY_KEY] });
    },
  });
}

/**
 * Não é um useQuery normal de propósito — o link assinado expira em 15
 * minutos, então gerar um novo a cada clique em "baixar" (em vez de
 * cachear um link que pode já estar vencido) é o comportamento certo
 * aqui.
 */
export function useDownloadFinanceAttachment() {
  return useMutation({
    mutationFn: (transactionId: string) => getFinanceAttachmentDownloadUrl(transactionId),
  });
}
