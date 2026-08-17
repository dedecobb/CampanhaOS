import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { clearVoterGoal, getDashboardStats, setVoterGoal } from "@/features/dashboard/api/dashboard-api";

const DASHBOARD_STATS_QUERY_KEY = "dashboard-stats";

export function useDashboardStats() {
  return useQuery({
    queryKey: [DASHBOARD_STATS_QUERY_KEY],
    queryFn: getDashboardStats,
  });
}

export function useSetVoterGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: setVoterGoal,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [DASHBOARD_STATS_QUERY_KEY] });
    },
  });
}

export function useClearVoterGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: clearVoterGoal,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [DASHBOARD_STATS_QUERY_KEY] });
    },
  });
}
