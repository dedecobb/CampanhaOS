import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createEvent, deleteEvent, getEvent, listEvents, updateEvent } from "@/features/events/api/events-api";
import type { EventCreateRequest, EventListParams, EventUpdateRequest } from "@/features/events/api/types";

const EVENTS_QUERY_KEY = "events";

export function useEvents(params: EventListParams) {
  return useQuery({
    queryKey: [EVENTS_QUERY_KEY, params],
    queryFn: () => listEvents(params),
  });
}

export function useEvent(id: string | undefined) {
  return useQuery({
    queryKey: [EVENTS_QUERY_KEY, id],
    queryFn: () => getEvent(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EventCreateRequest) => createEvent(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [EVENTS_QUERY_KEY] });
    },
  });
}

export function useUpdateEvent(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EventUpdateRequest) => updateEvent(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [EVENTS_QUERY_KEY] });
    },
  });
}

export function useDeleteEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteEvent(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [EVENTS_QUERY_KEY] });
    },
  });
}
