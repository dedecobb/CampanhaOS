/**
 * Espelha src/presentation/api/v1/schemas/events.py do backend.
 *
 * Nota de escopo (mesma decisão do leadership_id em Voter, Módulo 5): o
 * formulário não expõe associação com eleitor/liderança nem
 * responsible_user_id — o backend aceita esses campos, mas a tela
 * cobre só o fluxo mais comum (agendar um evento simples). Associação
 * fica pra uma melhoria futura.
 */

export const EVENT_TYPE_OPTIONS = [
  { value: "evento", label: "Evento" },
  { value: "reuniao", label: "Reunião" },
  { value: "visita", label: "Visita" },
] as const;

export const EVENT_STATUS_OPTIONS = [
  { value: "agendado", label: "Agendado" },
  { value: "concluido", label: "Concluído" },
  { value: "cancelado", label: "Cancelado" },
] as const;

export interface Event {
  id: string;
  created_by_user_id: string;
  responsible_user_id: string;
  title: string;
  description: string | null;
  event_type: string;
  status: string;
  location: string | null;
  starts_at: string;
  ends_at: string | null;
  voter_id: string | null;
  leadership_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface EventListResponse {
  items: Event[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface EventFormValues {
  title: string;
  event_type: string;
  status: string; // só usado no modo edição — criação sempre começa "agendado" no backend
  starts_at: string; // formato datetime-local do HTML
  ends_at: string;
  location: string;
  description: string;
}

export interface EventCreateRequest {
  title: string;
  event_type: string;
  starts_at: string;
  description?: string | null;
  location?: string | null;
  ends_at?: string | null;
}

export interface EventUpdateRequest {
  title?: string;
  description?: string | null;
  event_type?: string;
  status?: string;
  location?: string | null;
  starts_at?: string;
  ends_at?: string | null;
}

export interface EventListParams {
  search?: string;
  event_type?: string;
  status?: string;
  page?: number;
  page_size?: number;
}
