import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createFinanceTransaction,
  deleteFinanceTransaction,
  getFinanceTransaction,
  listFinanceTransactions,
  updateFinanceTransaction,
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
