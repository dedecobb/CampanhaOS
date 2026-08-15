import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createLeadership,
  deleteLeadership,
  getLeadership,
  listLeaderships,
  updateLeadership,
} from "@/features/leaderships/api/leaderships-api";
import type {
  LeadershipCreateRequest,
  LeadershipListParams,
  LeadershipUpdateRequest,
} from "@/features/leaderships/api/types";

const LEADERSHIPS_QUERY_KEY = "leaderships";

export function useLeaderships(params: LeadershipListParams) {
  return useQuery({
    queryKey: [LEADERSHIPS_QUERY_KEY, params],
    queryFn: () => listLeaderships(params),
  });
}

export function useLeadership(id: string | undefined) {
  return useQuery({
    queryKey: [LEADERSHIPS_QUERY_KEY, id],
    queryFn: () => getLeadership(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateLeadership() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: LeadershipCreateRequest) => createLeadership(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [LEADERSHIPS_QUERY_KEY] });
    },
  });
}

export function useUpdateLeadership(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: LeadershipUpdateRequest) => updateLeadership(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [LEADERSHIPS_QUERY_KEY] });
    },
  });
}

export function useDeleteLeadership() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteLeadership(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [LEADERSHIPS_QUERY_KEY] });
    },
  });
}
