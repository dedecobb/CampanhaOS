import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select } from "@/shared/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import { useDeleteFinanceTransaction, useFinanceTransactions } from "@/features/finance/hooks/use-finance";
import { TRANSACTION_TYPE_OPTIONS, formatCurrencyFromString } from "@/features/finance/api/types";

const PAGE_SIZE = 20;

/**
 * `occurred_at` é uma data SEM hora (ex: "2026-08-18") — passar essa
 * string direto pro construtor `new Date(...)` faz o JavaScript
 * interpretar como meia-noite em UTC, e `.toLocaleDateString()` depois
 * mostra isso no fuso LOCAL do navegador. Como o Brasil fica atrás do
 * UTC, meia-noite UTC de um dia vira noite do dia ANTERIOR aqui — a
 * data "volta" um dia na tela, mesmo estando correta no banco.
 *
 * Construir a data com ano/mês/dia separados (em vez de string ISO)
 * evita isso — esse construtor usa hora LOCAL diretamente, sem passar
 * por UTC no meio do caminho.
 */
function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString("pt-BR");
}

export function FinanceTransactionsListPage() {
  const [typeFilter, setTypeFilter] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useFinanceTransactions({
    type: typeFilter || undefined,
    page,
    page_size: PAGE_SIZE,
  });
  const deleteTransaction = useDeleteFinanceTransaction();

  async function handleDelete(id: string, category: string) {
    if (window.confirm(`Excluir o lançamento "${category}"? Esta ação não pode ser desfeita.`)) {
      await deleteTransaction.mutateAsync(id);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Financeiro</h1>
        <Button asChild>
          <Link to="/financeiro/novo">Novo Lançamento</Link>
        </Button>
      </div>

      {/*
        Aviso de compliance (ADR-010, documento fonte da verdade): este
        módulo é controle INTERNO — não substitui a prestação de contas
        oficial ao TSE, que é feita via Conta+JE.
      */}
      <p className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-400">
        Este módulo é controle financeiro interno da campanha. A prestação de contas oficial ao TSE continua
        sendo feita separadamente, pelo sistema Conta+JE.
      </p>

      {data && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Receitas</CardTitle>
            </CardHeader>
            <CardContent className="text-xl font-semibold text-emerald-600">
              {formatCurrencyFromString(data.summary.total_receitas)}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Despesas</CardTitle>
            </CardHeader>
            <CardContent className="text-xl font-semibold text-destructive">
              {formatCurrencyFromString(data.summary.total_despesas)}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Doações</CardTitle>
            </CardHeader>
            <CardContent className="text-xl font-semibold text-emerald-600">
              {formatCurrencyFromString(data.summary.total_doacoes)}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Saldo</CardTitle>
            </CardHeader>
            <CardContent className="text-xl font-semibold">
              {formatCurrencyFromString(data.summary.saldo)}
            </CardContent>
          </Card>
        </div>
      )}

      <Select
        value={typeFilter}
        onChange={(e) => {
          setTypeFilter(e.target.value);
          setPage(1);
        }}
        className="max-w-xs"
      >
        <option value="">Todos os tipos</option>
        {TRANSACTION_TYPE_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </Select>

      {isLoading && <p className="text-muted-foreground">Carregando...</p>}
      {isError && <p className="text-destructive">Não foi possível carregar os lançamentos.</p>}

      {data && (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Categoria</TableHead>
                <TableHead className="text-right">Valor</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    Nenhum lançamento encontrado.
                  </TableCell>
                </TableRow>
              )}
              {data.items.map((transaction) => (
                <TableRow key={transaction.id}>
                  <TableCell>{formatDate(transaction.occurred_at)}</TableCell>
                  <TableCell className="capitalize">{transaction.type}</TableCell>
                  <TableCell className="font-medium">{transaction.category}</TableCell>
                  <TableCell className="text-right">{formatCurrencyFromString(transaction.amount)}</TableCell>
                  <TableCell className="space-x-2 text-right">
                    <Button variant="outline" size="sm" asChild>
                      <Link to={`/financeiro/${transaction.id}/editar`}>Editar</Link>
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(transaction.id, transaction.category)}
                      disabled={deleteTransaction.isPending}
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
              Página {data.page} de {Math.max(data.total_pages, 1)} — {data.total} lançamento(s)
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
