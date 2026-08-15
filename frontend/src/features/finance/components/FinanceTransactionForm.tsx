import { useState, type FormEvent } from "react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Select } from "@/shared/components/ui/select";
import {
  TRANSACTION_TYPE_OPTIONS,
  type FinanceTransaction,
  type FinanceTransactionFormValues,
} from "@/features/finance/api/types";

interface FinanceTransactionFormProps {
  initialTransaction?: FinanceTransaction;
  onSubmit: (values: FinanceTransactionFormValues) => Promise<void>;
  isSubmitting: boolean;
  submitLabel: string;
}

// Só dígitos, opcionalmente um ponto decimal com até 2 casas — mesma
// regra de precisão que o backend exige (NUMERIC(12,2)), validada aqui
// como TEXTO, nunca convertendo pra number (ver nota em api/types.ts).
const AMOUNT_PATTERN = /^\d+(\.\d{1,2})?$/;

function todayAsDateInputValue(): string {
  return new Date().toISOString().split("T")[0];
}

function transactionToFormValues(transaction: FinanceTransaction | undefined): FinanceTransactionFormValues {
  return {
    type: transaction?.type ?? TRANSACTION_TYPE_OPTIONS[0].value,
    category: transaction?.category ?? "",
    amount: transaction?.amount ?? "",
    occurred_at: transaction?.occurred_at ?? todayAsDateInputValue(),
    description: transaction?.description ?? "",
  };
}

export function FinanceTransactionForm({
  initialTransaction,
  onSubmit,
  isSubmitting,
  submitLabel,
}: FinanceTransactionFormProps) {
  const [values, setValues] = useState<FinanceTransactionFormValues>(transactionToFormValues(initialTransaction));
  const [error, setError] = useState<string | null>(null);

  function updateField<K extends keyof FinanceTransactionFormValues>(field: K, value: FinanceTransactionFormValues[K]) {
    setValues((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!values.category.trim()) {
      setError("Categoria é obrigatória.");
      return;
    }
    if (!AMOUNT_PATTERN.test(values.amount) || Number(values.amount) <= 0) {
      // Number() aqui é só pra checar > 0 na validação da tela — o valor
      // que efetivamente vai pra API continua sendo a string original,
      // sem passar por essa conversão (ver handleSubmit do FormPage).
      setError("Valor precisa ser um número positivo, com até 2 casas decimais (ex: 150.00).");
      return;
    }
    await onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="type">Tipo</Label>
        <Select id="type" value={values.type} onChange={(e) => updateField("type", e.target.value)}>
          {TRANSACTION_TYPE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="category">Categoria</Label>
        <Input
          id="category"
          value={values.category}
          onChange={(e) => updateField("category", e.target.value)}
          placeholder="ex: Doação PF, Combustível, Material gráfico"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="amount">Valor (R$)</Label>
          <Input
            id="amount"
            type="text"
            inputMode="decimal"
            value={values.amount}
            onChange={(e) => updateField("amount", e.target.value)}
            placeholder="150.00"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="occurred_at">Data</Label>
          <Input
            id="occurred_at"
            type="date"
            value={values.occurred_at}
            onChange={(e) => updateField("occurred_at", e.target.value)}
          />
        </div>
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
