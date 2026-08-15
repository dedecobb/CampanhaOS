import { useState, type FormEvent } from "react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Select } from "@/shared/components/ui/select";
import { EVENT_STATUS_OPTIONS, EVENT_TYPE_OPTIONS, type Event, type EventFormValues } from "@/features/events/api/types";

interface EventFormProps {
  initialEvent?: Event;
  onSubmit: (values: EventFormValues) => Promise<void>;
  isSubmitting: boolean;
  submitLabel: string;
  /** Só mostra o campo de status em modo edição — criação sempre começa "agendado" no backend. */
  showStatusField: boolean;
}

/**
 * Converte um datetime ISO (vindo da API) para o formato que o
 * <input type="datetime-local"> do HTML entende (sem segundos, sem
 * timezone explícito — o navegador trata como horário local).
 */
function isoToDatetimeLocal(iso: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/** Converte de volta o valor do input para ISO, que é o que a API espera. */
function datetimeLocalToIso(value: string): string {
  return new Date(value).toISOString();
}

function eventToFormValues(event: Event | undefined): EventFormValues {
  return {
    title: event?.title ?? "",
    event_type: event?.event_type ?? EVENT_TYPE_OPTIONS[0].value,
    status: event?.status ?? EVENT_STATUS_OPTIONS[0].value,
    starts_at: isoToDatetimeLocal(event?.starts_at ?? null),
    ends_at: isoToDatetimeLocal(event?.ends_at ?? null),
    location: event?.location ?? "",
    description: event?.description ?? "",
  };
}

export function EventForm({ initialEvent, onSubmit, isSubmitting, submitLabel, showStatusField }: EventFormProps) {
  const [values, setValues] = useState<EventFormValues>(eventToFormValues(initialEvent));
  const [error, setError] = useState<string | null>(null);

  function updateField<K extends keyof EventFormValues>(field: K, value: EventFormValues[K]) {
    setValues((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!values.title.trim()) {
      setError("Título é obrigatório.");
      return;
    }
    if (!values.starts_at) {
      setError("Data/hora de início é obrigatória.");
      return;
    }
    await onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="title">Título</Label>
        <Input id="title" value={values.title} onChange={(e) => updateField("title", e.target.value)} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="event_type">Tipo</Label>
          <Select id="event_type" value={values.event_type} onChange={(e) => updateField("event_type", e.target.value)}>
            {EVENT_TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>
        {showStatusField && (
          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <Select id="status" value={values.status} onChange={(e) => updateField("status", e.target.value)}>
              {EVENT_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="starts_at">Início</Label>
          <Input
            id="starts_at"
            type="datetime-local"
            value={values.starts_at}
            onChange={(e) => updateField("starts_at", e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="ends_at">Fim</Label>
          <Input
            id="ends_at"
            type="datetime-local"
            value={values.ends_at}
            onChange={(e) => updateField("ends_at", e.target.value)}
            placeholder="Opcional"
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="location">Local</Label>
        <Input id="location" value={values.location} onChange={(e) => updateField("location", e.target.value)} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Descrição</Label>
        <textarea
          id="description"
          value={values.description}
          onChange={(e) => updateField("description", e.target.value)}
          className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        />
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Salvando..." : submitLabel}
      </Button>
    </form>
  );
}

export { datetimeLocalToIso };
