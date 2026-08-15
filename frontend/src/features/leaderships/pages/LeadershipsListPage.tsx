import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import { useDeleteLeadership, useLeaderships } from "@/features/leaderships/hooks/use-leaderships";

const PAGE_SIZE = 20;

export function LeadershipsListPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useLeaderships({ search: search || undefined, page, page_size: PAGE_SIZE });
  const deleteLeadership = useDeleteLeadership();

  async function handleDelete(id: string, name: string) {
    if (window.confirm(`Excluir a liderança "${name}"? Esta ação não pode ser desfeita.`)) {
      await deleteLeadership.mutateAsync(id);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Lideranças</h1>
        <Button asChild>
          <Link to="/liderancas/novo">Nova Liderança</Link>
        </Button>
      </div>

      <Input
        placeholder="Buscar por nome ou região..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
        className="max-w-sm"
      />

      {isLoading && <p className="text-muted-foreground">Carregando...</p>}
      {isError && <p className="text-destructive">Não foi possível carregar as lideranças.</p>}

      {data && (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>Região</TableHead>
                <TableHead>Influência</TableHead>
                <TableHead>Votos estimados</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    Nenhuma liderança encontrada.
                  </TableCell>
                </TableRow>
              )}
              {data.items.map((leadership) => (
                <TableRow key={leadership.id}>
                  <TableCell className="font-medium">{leadership.name}</TableCell>
                  <TableCell>{leadership.region ?? "—"}</TableCell>
                  <TableCell className="capitalize">{leadership.influence_level}</TableCell>
                  <TableCell>{leadership.estimated_votes}</TableCell>
                  <TableCell className="space-x-2 text-right">
                    <Button variant="outline" size="sm" asChild>
                      <Link to={`/liderancas/${leadership.id}/editar`}>Editar</Link>
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(leadership.id, leadership.name)}
                      disabled={deleteLeadership.isPending}
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
              Página {data.page} de {Math.max(data.total_pages, 1)} — {data.total} liderança(s)
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
