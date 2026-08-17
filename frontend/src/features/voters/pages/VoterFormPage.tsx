import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { getApiErrorMessage } from "@/shared/lib/api-client";
import { VoterForm } from "@/features/voters/components/VoterForm";
import { useCreateVoter, useUpdateVoter, useVoter } from "@/features/voters/hooks/use-voters";
import type { VoterFormValues } from "@/features/voters/api/types";

/**
 * Uma página só para os dois casos (criar/editar) — evita duplicar o
 * layout e a lógica de conversão de formulário -> request entre duas
 * páginas quase idênticas. O `id` vindo da URL (`useParams`) é o que
 * decide qual modo está ativo.
 */
export function VoterFormPage() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);

  const { data: existingVoter, isLoading: isLoadingVoter } = useVoter(id);
  const createVoter = useCreateVoter();
  const updateVoter = useUpdateVoter(id ?? "");
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleSubmit(values: VoterFormValues) {
    setSubmitError(null);

    const tags = values.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);

    const payload = {
      name: values.name,
      legal_basis: values.legal_basis,
      phone: values.phone || null,
      address: values.address || null,
      city: values.city || null,
      state: values.state || null,
      postal_code: values.postal_code || null,
      neighborhood: values.neighborhood || null,
      gender: values.gender || null,
      birth_date: values.birth_date || null,
      tags,
      notes: values.notes || null,
      ...(values.locationManuallyAdjusted
        ? { latitude: values.latitude, longitude: values.longitude }
        : {}),
    };

    try {
      if (isEditMode) {
        await updateVoter.mutateAsync(payload);
      } else {
        await createVoter.mutateAsync(payload);
      }
      navigate("/eleitores");
    } catch (error) {
      // Antes disso, um erro aqui desaparecia silenciosamente — a
      // pessoa via o formulário "não fazer nada" sem entender por quê.
      setSubmitError(getApiErrorMessage(error));
    }
  }

  if (isEditMode && isLoadingVoter) {
    return <p className="text-muted-foreground">Carregando eleitor...</p>;
  }

  return (
    <div className="mx-auto max-w-lg">
      <Card>
        <CardHeader>
          <CardTitle>{isEditMode ? "Editar Eleitor" : "Novo Eleitor"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {submitError && (
            <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {submitError}
            </p>
          )}
          <VoterForm
            initialVoter={existingVoter}
            onSubmit={handleSubmit}
            isSubmitting={createVoter.isPending || updateVoter.isPending}
            submitLabel={isEditMode ? "Salvar alterações" : "Cadastrar eleitor"}
          />
        </CardContent>
      </Card>
    </div>
  );
}

