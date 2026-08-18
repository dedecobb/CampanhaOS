import { useNavigate, useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { LeadershipForm } from "@/features/leaderships/components/LeadershipForm";
import { LeadershipRegistrationLinkSection } from "@/features/leaderships/components/LeadershipRegistrationLinkSection";
import { useCreateLeadership, useLeadership, useUpdateLeadership } from "@/features/leaderships/hooks/use-leaderships";
import type { LeadershipFormValues } from "@/features/leaderships/api/types";

export function LeadershipFormPage() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);

  const { data: existingLeadership, isLoading: isLoadingLeadership } = useLeadership(id);
  const createLeadership = useCreateLeadership();
  const updateLeadership = useUpdateLeadership(id ?? "");

  async function handleSubmit(values: LeadershipFormValues) {
    const payload = {
      name: values.name,
      influence_level: values.influence_level,
      region: values.region || null,
      estimated_votes: values.estimated_votes ? Number(values.estimated_votes) : 0,
      team_size: values.team_size ? Number(values.team_size) : null,
      notes: values.notes || null,
    };

    if (isEditMode) {
      await updateLeadership.mutateAsync(payload);
      navigate("/liderancas");
    } else {
      // Depois de CRIAR, vai direto pra edição da liderança recém-criada
      // (não pra lista) — é ali que o link de cadastro dela aparece, e o
      // fluxo combinado é "assim que cadastra, já tem o link pronto pra
      // mandar pro líder".
      const created = await createLeadership.mutateAsync(payload);
      navigate(`/liderancas/${created.id}/editar`);
    }
  }

  if (isEditMode && isLoadingLeadership) {
    return <p className="text-muted-foreground">Carregando liderança...</p>;
  }

  return (
    <div className="mx-auto max-w-lg">
      <Card>
        <CardHeader>
          <CardTitle>{isEditMode ? "Editar Liderança" : "Nova Liderança"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <LeadershipForm
            initialLeadership={existingLeadership}
            onSubmit={handleSubmit}
            isSubmitting={createLeadership.isPending || updateLeadership.isPending}
            submitLabel={isEditMode ? "Salvar alterações" : "Cadastrar liderança"}
          />
          {isEditMode && existingLeadership && (
            <LeadershipRegistrationLinkSection leadershipId={existingLeadership.id} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
