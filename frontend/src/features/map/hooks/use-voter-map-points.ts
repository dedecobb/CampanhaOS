import { useQuery } from "@tanstack/react-query";
import { listVoterMapPoints } from "@/features/map/api/map-api";

export function useVoterMapPoints() {
  return useQuery({
    queryKey: ["voter-map-points"],
    queryFn: listVoterMapPoints,
  });
}
