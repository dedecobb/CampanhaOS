import { useNavigate, useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { EventForm, datetimeLocalToIso } from "@/features/events/components/EventForm";
import { useCreateEvent, useEvent, useUpdateEvent } from "@/features/events/hooks/use-events";
import type { EventFormValues } from "@/features/events/api/types";

export function EventFormPage() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);

  const { data: existingEvent, isLoading: isLoadingEvent } = useEvent(id);
  const createEvent = useCreateEvent();
  const updateEvent = useUpdateEvent(id ?? "");

  async function handleSubmit(values: EventFormValues) {
    const basePayload = {
      title: values.title,
      event_type: values.event_type,
      starts_at: datetimeLocalToIso(values.starts_at),
      ends_at: values.ends_at ? datetimeLocalToIso(values.ends_at) : null,
      location: values.location || null,
      description: values.description || null,
    };

    if (isEditMode) {
      await updateEvent.mutateAsync({ ...basePayload, status: values.status });
    } else {
      await createEvent.mutateAsync(basePayload);
    }
    navigate("/agenda");
  }

  if (isEditMode && isLoadingEvent) {
    return <p className="text-muted-foreground">Carregando evento...</p>;
  }

  return (
    <div className="mx-auto max-w-lg">
      <Card>
        <CardHeader>
          <CardTitle>{isEditMode ? "Editar Evento" : "Novo Evento"}</CardTitle>
        </CardHeader>
        <CardContent>
          <EventForm
            initialEvent={existingEvent}
            onSubmit={handleSubmit}
            isSubmitting={createEvent.isPending || updateEvent.isPending}
            submitLabel={isEditMode ? "Salvar alterações" : "Cadastrar evento"}
            showStatusField={isEditMode}
          />
        </CardContent>
      </Card>
    </div>
  );
}
