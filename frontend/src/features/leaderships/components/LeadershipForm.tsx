import { useState, type FormEvent } from "react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Select } from "@/shared/components/ui/select";
import { INFLUENCE_LEVEL_OPTIONS, type Leadership, type LeadershipFormValues } from "@/features/leaderships/api/types";

interface LeadershipFormProps {
  initialLeadership?: Leadership;
  onSubmit: (values: LeadershipFormValues) => Promise<void>;
  isSubmitting: boolean;
  submitLabel: string;
}

function leadershipToFormValues(leadership: Leadership | undefined): LeadershipFormValues {
  return {
    name: leadership?.name ?? "",
    influence_level: leadership?.influence_level ?? INFLUENCE_LEVEL_OPTIONS[0].value,
    region: leadership?.region ?? "",
    estimated_votes: leadership ? String(leadership.estimated_votes) : "0",
    team_size: leadership?.team_size != null ? String(leadership.team_size) : "",
    notes: leadership?.notes ?? "",
  };
}

export function LeadershipForm({ initialLeadership, onSubmit, isSubmitting, submitLabel }: LeadershipFormProps) {
  const [values, setValues] = useState<LeadershipFormValues>(leadershipToFormValues(initialLeadership));
  const [error, setError] = useState<string | null>(null);

  function updateField<K extends keyof LeadershipFormValues>(field: K, value: LeadershipFormValues[K]) {
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
        <Label htmlFor="influence_level">Nível de influência</Label>
        <Select
          id="influence_level"
          value={values.influence_level}
          onChange={(e) => updateField("influence_level", e.target.value)}
        >
          {INFLUENCE_LEVEL_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="region">Região</Label>
        <Input id="region" value={values.region} onChange={(e) => updateField("region", e.target.value)} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="estimated_votes">Votos estimados</Label>
          <Input
            id="estimated_votes"
            type="number"
            min="0"
            value={values.estimated_votes}
            onChange={(e) => updateField("estimated_votes", e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="team_size">Tamanho da equipe</Label>
          <Input
            id="team_size"
            type="number"
            min="0"
            value={values.team_size}
            onChange={(e) => updateField("team_size", e.target.value)}
            placeholder="Opcional"
          />
        </div>
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
