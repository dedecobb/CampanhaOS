import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createVoter,
  deleteVoter,
  getVoter,
  listVoters,
  updateVoter,
} from "@/features/voters/api/voters-api";
import type { VoterListParams, VoterUpdateRequest, VoterCreateRequest } from "@/features/voters/api/types";

const VOTERS_QUERY_KEY = "voters";

export function useVoters(params: VoterListParams) {
  return useQuery({
    queryKey: [VOTERS_QUERY_KEY, params],
    queryFn: () => listVoters(params),
  });
}

export function useVoter(id: string | undefined) {
  return useQuery({
    queryKey: [VOTERS_QUERY_KEY, id],
    queryFn: () => getVoter(id as string),
    // Só dispara a busca se um id de verdade foi passado — usado na
    // página de formulário, onde o modo "criação" não tem id nenhum.
    enabled: Boolean(id),
  });
}

export function useCreateVoter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: VoterCreateRequest) => createVoter(data),
    onSuccess: () => {
      // Invalida a listagem em cache — a próxima vez que a lista for
      // exibida, o React Query busca de novo, já incluindo o novo registro.
      void queryClient.invalidateQueries({ queryKey: [VOTERS_QUERY_KEY] });
    },
  });
}

export function useUpdateVoter(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: VoterUpdateRequest) => updateVoter(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [VOTERS_QUERY_KEY] });
    },
  });
}

export function useDeleteVoter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteVoter(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [VOTERS_QUERY_KEY] });
    },
  });
}
