import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/components/ui/table";
import { useDeleteVoter, useVoters } from "@/features/voters/hooks/use-voters";
import type { Voter } from "@/features/voters/api/types";

const PAGE_SIZE = 20;

export function VotersListPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useVoters({ search: search || undefined, page, page_size: PAGE_SIZE });
  const deleteVoter = useDeleteVoter();

  async function handleDelete(id: string, name: string) {
    if (window.confirm(`Excluir o eleitor "${name}"? Esta ação não pode ser desfeita.`)) {
      await deleteVoter.mutateAsync(id);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
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
          setPage(1);
        }}
        className="max-w-sm"
      />

      {isLoading && <p className="text-muted-foreground">Carregando...</p>}
      {isError && <p className="text-destructive">Não foi possível carregar os eleitores.</p>}

      {data && (
        <>
          {data.items.length === 0 && (
            <p className="py-8 text-center text-muted-foreground">Nenhum eleitor encontrado.</p>
          )}

          {/* Computador (md e acima): tabela tradicional — escondida no celular. */}
          {data.items.length > 0 && (
            <div className="hidden md:block">
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
            </div>
          )}

          {/* Celular (abaixo de md): cartões empilhados — mesma informação e
              ações da tabela, só que numa forma que não precisa rolar de
              lado pra ler (rolar tabela pro lado é uma experiência ruim
              em tela pequena). Escondido no computador. */}
          <div className="space-y-3 md:hidden">
            {data.items.map((voter) => (
              <VoterCard
                key={voter.id}
                voter={voter}
                onDelete={() => handleDelete(voter.id, voter.name)}
                isDeleting={deleteVoter.isPending}
              />
            ))}
          </div>

          <div className="flex flex-col gap-3 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
            <span>
              Página {data.page} de {Math.max(data.total_pages, 1)} — {data.total} eleitor(es)
            </span>
            <div className="flex gap-2">
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

interface VoterCardProps {
  voter: Voter;
  onDelete: () => void;
  isDeleting: boolean;
}

function VoterCard({ voter, onDelete, isDeleting }: VoterCardProps) {
  return (
    <div className="rounded-lg border border-border p-4">
      <p className="font-medium">{voter.name}</p>
      <p className="mt-1 text-sm text-muted-foreground">{voter.phone ?? "Sem telefone"}</p>
      {voter.tags.length > 0 && <p className="mt-1 text-xs text-muted-foreground">{voter.tags.join(", ")}</p>}
      <div className="mt-3 flex gap-2">
        <Button variant="outline" size="sm" asChild className="flex-1">
          <Link to={`/eleitores/${voter.id}/editar`}>Editar</Link>
        </Button>
        <Button variant="destructive" size="sm" onClick={onDelete} disabled={isDeleting} className="flex-1">
          Excluir
        </Button>
      </div>
    </div>
  );
}
