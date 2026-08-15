import { apiClient } from "@/shared/lib/api-client";
import type {
  Event,
  EventCreateRequest,
  EventListParams,
  EventListResponse,
  EventUpdateRequest,
} from "@/features/events/api/types";

export async function listEvents(params: EventListParams): Promise<EventListResponse> {
  const response = await apiClient.get<EventListResponse>("/events", { params });
  return response.data;
}

export async function getEvent(id: string): Promise<Event> {
  const response = await apiClient.get<Event>(`/events/${id}`);
  return response.data;
}

export async function createEvent(data: EventCreateRequest): Promise<Event> {
  const response = await apiClient.post<Event>("/events", data);
  return response.data;
}

export async function updateEvent(id: string, data: EventUpdateRequest): Promise<Event> {
  const response = await apiClient.patch<Event>(`/events/${id}`, data);
  return response.data;
}

export async function deleteEvent(id: string): Promise<void> {
  await apiClient.delete(`/events/${id}`);
}
