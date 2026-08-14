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
import { useDeleteVoter, useVoters } from "@/features/voters/hooks/use-voters";

const PAGE_SIZE = 20;

export function VotersListPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useVoters({ search: search || undefined, page, page_size: PAGE_SIZE });
  const deleteVoter = useDeleteVoter();

  async function handleDelete(id: string, name: string) {
    // Confirmação simples via `confirm` nativo — suficiente para o MVP;
    // um modal de confirmação mais elaborado é uma melhoria de UX futura,
    // não uma necessidade funcional.
    if (window.confirm(`Excluir o eleitor "${name}"? Esta ação não pode ser desfeita.`)) {
      await deleteVoter.mutateAsync(id);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Eleitores</h1>
        <Button asChild>
          <Link to="/eleitores/novo">Novo Eleitor</Link>
        </Button>
      </div>

      <Input
        placeholder="Buscar por nome ou telefone..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1); // volta pra primeira página a cada nova busca
        }}
        className="max-w-sm"
      />

      {isLoading && <p className="text-muted-foreground">Carregando...</p>}
      {isError && <p className="text-destructive">Não foi possível carregar os eleitores.</p>}

      {data && (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>Telefone</TableHead>
                <TableHead>Tags</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    Nenhum eleitor encontrado.
                  </TableCell>
                </TableRow>
              )}
              {data.items.map((voter) => (
                <TableRow key={voter.id}>
                  <TableCell className="font-medium">{voter.name}</TableCell>
                  <TableCell>{voter.phone ?? "—"}</TableCell>
                  <TableCell>{voter.tags.join(", ") || "—"}</TableCell>
                  <TableCell className="space-x-2 text-right">
                    <Button variant="outline" size="sm" asChild>
                      <Link to={`/eleitores/${voter.id}/editar`}>Editar</Link>
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(voter.id, voter.name)}
                      disabled={deleteVoter.isPending}
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
              Página {data.page} de {Math.max(data.total_pages, 1)} — {data.total} eleitor(es)
            </span>
            <div className="space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page <= 1}
              >
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
