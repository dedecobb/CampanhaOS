import { useNavigate, useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { FinanceTransactionForm } from "@/features/finance/components/FinanceTransactionForm";
import {
  useCreateFinanceTransaction,
  useFinanceTransaction,
  useUpdateFinanceTransaction,
} from "@/features/finance/hooks/use-finance";
import type { FinanceTransactionFormValues } from "@/features/finance/api/types";

export function FinanceTransactionFormPage() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);

  const { data: existingTransaction, isLoading: isLoadingTransaction } = useFinanceTransaction(id);
  const createTransaction = useCreateFinanceTransaction();
  const updateTransaction = useUpdateFinanceTransaction(id ?? "");

  async function handleSubmit(values: FinanceTransactionFormValues) {
    // `amount` continua string do formulário direto pra API — nunca
    // passa por Number() (ver nota de precisão em api/types.ts).
    const payload = {
      type: values.type,
      category: values.category,
      amount: values.amount,
      occurred_at: values.occurred_at,
      description: values.description || null,
    };

    if (isEditMode) {
      await updateTransaction.mutateAsync(payload);
    } else {
      await createTransaction.mutateAsync(payload);
    }
    navigate("/financeiro");
  }

  if (isEditMode && isLoadingTransaction) {
    return <p className="text-muted-foreground">Carregando lançamento...</p>;
  }

  return (
    <div className="mx-auto max-w-lg">
      <Card>
        <CardHeader>
          <CardTitle>{isEditMode ? "Editar Lançamento" : "Novo Lançamento"}</CardTitle>
        </CardHeader>
        <CardContent>
          <FinanceTransactionForm
            initialTransaction={existingTransaction}
            onSubmit={handleSubmit}
            isSubmitting={createTransaction.isPending || updateTransaction.isPending}
            submitLabel={isEditMode ? "Salvar alterações" : "Cadastrar lançamento"}
          />
        </CardContent>
      </Card>
    </div>
  );
}
