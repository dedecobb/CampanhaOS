import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/shared/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import { useDeleteEvent, useEvents } from "@/features/events/hooks/use-events";

const PAGE_SIZE = 20;

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export function EventsListPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useEvents({ page, page_size: PAGE_SIZE });
  const deleteEvent = useDeleteEvent();

  async function handleDelete(id: string, title: string) {
    if (window.confirm(`Excluir o evento "${title}"? Esta ação não pode ser desfeita.`)) {
      await deleteEvent.mutateAsync(id);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Agenda</h1>
        <Button asChild>
          <Link to="/agenda/novo">Novo Evento</Link>
        </Button>
      </div>

      {isLoading && <p className="text-muted-foreground">Carregando...</p>}
      {isError && <p className="text-destructive">Não foi possível carregar a agenda.</p>}

      {data && (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Título</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Início</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    Nenhum evento encontrado.
                  </TableCell>
                </TableRow>
              )}
              {data.items.map((event) => (
                <TableRow key={event.id}>
                  <TableCell className="font-medium">{event.title}</TableCell>
                  <TableCell className="capitalize">{event.event_type}</TableCell>
                  <TableCell>{formatDate(event.starts_at)}</TableCell>
                  <TableCell className="capitalize">{event.status}</TableCell>
                  <TableCell className="space-x-2 text-right">
                    <Button variant="outline" size="sm" asChild>
                      <Link to={`/agenda/${event.id}/editar`}>Editar</Link>
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(event.id, event.title)}
                      disabled={deleteEvent.isPending}
                    >
                      Excluir
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Página {data.page} de {Math.max(data.total_pages, 1)} — {data.total} evento(s)
            </span>
            <div className="space-x-2">
              <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(p - 1, 1))} disabled={page <= 1}>
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= data.total_pages}
              >
                Próxima
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
