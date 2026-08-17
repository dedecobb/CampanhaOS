import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  generateRegistrationLink,
  getRegistrationLink,
  revokeRegistrationLink,
} from "@/features/registration-link/api/registration-link-api";

const REGISTRATION_LINK_QUERY_KEY = "registration-link";

export function useRegistrationLink() {
  return useQuery({
    queryKey: [REGISTRATION_LINK_QUERY_KEY],
    queryFn: getRegistrationLink,
  });
}

export function useGenerateRegistrationLink() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: generateRegistrationLink,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [REGISTRATION_LINK_QUERY_KEY] });
    },
  });
}

export function useRevokeRegistrationLink() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: revokeRegistrationLink,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [REGISTRATION_LINK_QUERY_KEY] });
    },
  });
}
