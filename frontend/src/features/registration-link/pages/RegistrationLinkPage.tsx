import { useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import {
  useGenerateRegistrationLink,
  useRegistrationLink,
  useRevokeRegistrationLink,
} from "@/features/registration-link/hooks/use-registration-link";

export function RegistrationLinkPage() {
  const { data, isLoading } = useRegistrationLink();
  const generateLink = useGenerateRegistrationLink();
  const revokeLink = useRevokeRegistrationLink();
  const [copied, setCopied] = useState(false);

  async function handleGenerate() {
    // Regenerar quando já existe um link ativo invalida o antigo na
    // hora — deixamos isso claro antes de confirmar, já que alguém pode
    // já ter compartilhado o link atual em algum lugar.
    if (data?.token) {
      const confirmed = window.confirm(
        "Já existe um link ativo. Gerar um novo vai invalidar o link atual imediatamente — quem já tiver o link antigo não vai mais conseguir usá-lo. Continuar?",
      );
      if (!confirmed) return;
    }
    await generateLink.mutateAsync();
  }

  async function handleRevoke() {
    const confirmed = window.confirm(
      "Isso desativa o autocadastro público — o link atual para de funcionar imediatamente. Continuar?",
    );
    if (!confirmed) return;
    await revokeLink.mutateAsync();
  }

  async function handleCopy() {
    if (!data?.registration_url) return;
    await navigator.clipboard.writeText(data.registration_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h1 className="text-2xl font-semibold">Link de Autocadastro</h1>

      <Card>
        <CardHeader>
          <CardTitle>Como funciona</CardTitle>
          <CardDescription>
            Gere um link único e compartilhe com apoiadores (WhatsApp pessoal, redes sociais, etc.). Cada
            pessoa que abrir o link preenche o próprio cadastro, sem precisar de conta no sistema.
          </CardDescription>
        </CardHeader>
      </Card>

      {isLoading && <p className="text-muted-foreground">Carregando...</p>}

      {!isLoading && data && (
        <Card>
          <CardContent className="space-y-4 pt-6">
            {data.registration_url ? (
              <>
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <Input readOnly value={data.registration_url} className="font-mono text-xs" />
                    <Button variant="outline" onClick={handleCopy}>
                      {copied ? "Copiado!" : "Copiar"}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">Link ativo — qualquer pessoa com ele pode se cadastrar.</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleGenerate} disabled={generateLink.isPending}>
                    Gerar novo link (invalida o atual)
                  </Button>
                  <Button variant="destructive" onClick={handleRevoke} disabled={revokeLink.isPending}>
                    Desativar autocadastro
                  </Button>
                </div>
              </>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">Autocadastro público ainda não está ativado.</p>
                <Button onClick={handleGenerate} disabled={generateLink.isPending}>
                  {generateLink.isPending ? "Gerando..." : "Gerar link de autocadastro"}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
