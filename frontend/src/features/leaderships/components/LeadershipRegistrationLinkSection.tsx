import { useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { useRegistrationLink } from "@/features/registration-link/hooks/use-registration-link";

interface LeadershipRegistrationLinkSectionProps {
  leadershipId: string;
}

/**
 * Reaproveita o link ÚNICO da campanha (já existente), só adicionando um
 * parâmetro identificando a liderança — não existe token/link separado
 * por liderança, é o mesmo link geral + "?lideranca={id}" no final. Todo
 * apoiador que se cadastrar por essa URL específica já nasce vinculado a
 * esta liderança automaticamente (ver backend: public_self_register.py).
 */
export function LeadershipRegistrationLinkSection({ leadershipId }: LeadershipRegistrationLinkSectionProps) {
  const { data, isLoading } = useRegistrationLink();
  const [copied, setCopied] = useState(false);

  const leadershipLink = data?.registration_url ? `${data.registration_url}?lideranca=${leadershipId}` : null;

  async function handleCopy() {
    if (!leadershipLink) return;
    await navigator.clipboard.writeText(leadershipLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">Link de Cadastro desta Liderança</p>

      {isLoading && <p className="text-sm text-muted-foreground">Carregando...</p>}

      {!isLoading && !leadershipLink && (
        <p className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-400">
          O link de autocadastro da campanha ainda não foi ativado.{" "}
          <a href="/link-cadastro" className="underline">
            Ativa aqui primeiro
          </a>{" "}
          — depois volta nesta tela pra pegar o link desta liderança.
        </p>
      )}

      {leadershipLink && (
        <>
          <div className="flex gap-2">
            <Input readOnly value={leadershipLink} className="font-mono text-xs" />
            <Button type="button" variant="outline" onClick={handleCopy}>
              {copied ? "Copiado!" : "Copiar"}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Manda esse link pra essa liderança compartilhar com os apoiadores dela. Todo mundo que se
            cadastrar por ele já fica vinculado a ela automaticamente — sem precisar fazer nada manual.
          </p>
        </>
      )}
    </div>
  );
}
