import { useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { useClearVoterGoal, useSetVoterGoal } from "@/features/dashboard/hooks/use-dashboard-stats";

interface VoterGoalCardProps {
  totalVoters: number;
  voterGoal: number | null;
}

export function VoterGoalCard({ totalVoters, voterGoal }: VoterGoalCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [goalInput, setGoalInput] = useState(voterGoal?.toString() ?? "");
  const setGoal = useSetVoterGoal();
  const clearGoal = useClearVoterGoal();

  async function handleSave() {
    const goalNumber = Number(goalInput);
    if (!goalNumber || goalNumber <= 0) return;
    await setGoal.mutateAsync(goalNumber);
    setIsEditing(false);
  }

  if (isEditing) {
    return (
      <div className="flex items-center gap-2">
        <Input
          type="number"
          min="1"
          value={goalInput}
          onChange={(e) => setGoalInput(e.target.value)}
          placeholder="Ex: 5000"
          className="max-w-[140px]"
        />
        <Button size="sm" onClick={handleSave} disabled={setGoal.isPending}>
          Salvar
        </Button>
        <Button size="sm" variant="outline" onClick={() => setIsEditing(false)}>
          Cancelar
        </Button>
      </div>
    );
  }

  if (voterGoal === null) {
    return (
      <Button size="sm" variant="outline" onClick={() => setIsEditing(true)}>
        Definir meta de eleitores
      </Button>
    );
  }

  const percentage = Math.min(Math.round((totalVoters / voterGoal) * 100), 100);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          {totalVoters} de {voterGoal} eleitores ({percentage}%)
        </span>
        <div className="space-x-2">
          <button
            type="button"
            onClick={() => setIsEditing(true)}
            className="text-xs text-muted-foreground underline hover:text-foreground"
          >
            editar
          </button>
          <button
            type="button"
            onClick={() => clearGoal.mutate()}
            className="text-xs text-muted-foreground underline hover:text-foreground"
          >
            remover meta
          </button>
        </div>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
