import { useState, type FormEvent } from "react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Select } from "@/shared/components/ui/select";
import { LEGAL_BASIS_OPTIONS, type Voter, type VoterFormValues } from "@/features/voters/api/types";

interface VoterFormProps {
  initialVoter?: Voter;
  onSubmit: (values: VoterFormValues) => Promise<void>;
  isSubmitting: boolean;
  submitLabel: string;
}

function voterToFormValues(voter: Voter | undefined): VoterFormValues {
  return {
    name: voter?.name ?? "",
    legal_basis: voter?.legal_basis ?? LEGAL_BASIS_OPTIONS[0].value,
    phone: voter?.phone ?? "",
    address: voter?.address ?? "",
    city: voter?.city ?? "",
    state: voter?.state ?? "",
    postal_code: voter?.postal_code ?? "",
    neighborhood: voter?.neighborhood ?? "",
    tags: voter?.tags.join(", ") ?? "",
    notes: voter?.notes ?? "",
  };
}

export function VoterForm({ initialVoter, onSubmit, isSubmitting, submitLabel }: VoterFormProps) {
  const [values, setValues] = useState<VoterFormValues>(voterToFormValues(initialVoter));
  const [error, setError] = useState<string | null>(null);

  function updateField<K extends keyof VoterFormValues>(field: K, value: VoterFormValues[K]) {
    setValues((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!values.name.trim()) {
      setError("Nome é obrigatório.");
      return;
    }
    await onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Nome</Label>
        <Input id="name" value={values.name} onChange={(e) => updateField("name", e.target.value)} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="legal_basis">Base legal (LGPD)</Label>
        <Select
          id="legal_basis"
          value={values.legal_basis}
          onChange={(e) => updateField("legal_basis", e.target.value)}
        >
          {LEGAL_BASIS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="phone">Telefone</Label>
        <Input id="phone" value={values.phone} onChange={(e) => updateField("phone", e.target.value)} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="address">Endereço</Label>
        <Input id="address" value={values.address} onChange={(e) => updateField("address", e.target.value)} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="neighborhood">Bairro</Label>
        <Input
          id="neighborhood"
          value={values.neighborhood}
          onChange={(e) => updateField("neighborhood", e.target.value)}
        />
      </div>

      <div className="grid grid-cols-[1fr_auto_auto] gap-4">
        <div className="space-y-2">
          <Label htmlFor="city">Cidade</Label>
          <Input id="city" value={values.city} onChange={(e) => updateField("city", e.target.value)} />
        </div>
        <div className="w-20 space-y-2">
          <Label htmlFor="state">UF</Label>
          <Input
            id="state"
            value={values.state}
            onChange={(e) => updateField("state", e.target.value.toUpperCase())}
            maxLength={2}
            placeholder="RJ"
          />
        </div>
        <div className="w-32 space-y-2">
          <Label htmlFor="postal_code">CEP</Label>
          <Input
            id="postal_code"
            value={values.postal_code}
            onChange={(e) => updateField("postal_code", e.target.value)}
            placeholder="24000-000"
          />
        </div>
      </div>
      <p className="-mt-2 text-xs text-muted-foreground">
        Cidade, UF e CEP tornam a localização no mapa muito mais precisa — sem eles, o endereço sozinho pode
        ser confundido com uma rua de mesmo nome em outra cidade.
      </p>

      <div className="space-y-2">
        <Label htmlFor="tags">Tags (separadas por vírgula)</Label>
        <Input
          id="tags"
          value={values.tags}
          onChange={(e) => updateField("tags", e.target.value)}
          placeholder="lideranca, zona-norte"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="notes">Observações</Label>
        <textarea
          id="notes"
          value={values.notes}
          onChange={(e) => updateField("notes", e.target.value)}
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
