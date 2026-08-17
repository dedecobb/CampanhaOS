import { useRef, useState, type ChangeEvent } from "react";
import { Button } from "@/shared/components/ui/button";
import { formatFileSize, type FinanceTransaction } from "@/features/finance/api/types";
import { getApiErrorMessage } from "@/shared/lib/api-client";
import {
  useDownloadFinanceAttachment,
  useRemoveFinanceAttachment,
  useUploadFinanceAttachment,
} from "@/features/finance/hooks/use-finance";

interface FinanceAttachmentSectionProps {
  transaction: FinanceTransaction;
}

/**
 * Só faz sentido em modo de EDIÇÃO (precisa do id do lançamento já
 * existente) — mesmo raciocínio do LocationPicker (Módulo de Mapa):
 * ainda não existe nada pra anexar até o lançamento já estar salvo.
 */
export function FinanceAttachmentSection({ transaction }: FinanceAttachmentSectionProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const upload = useUploadFinanceAttachment(transaction.id);
  const remove = useRemoveFinanceAttachment(transaction.id);
  const download = useDownloadFinanceAttachment();

  async function handleFileSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadError(null);

    try {
      await upload.mutateAsync(file);
    } catch (error) {
      setUploadError(getApiErrorMessage(error));
    } finally {
      // Limpa o input — sem isso, selecionar o MESMO arquivo de novo
      // depois de um erro não dispara onChange (o navegador não
      // considera isso uma mudança de valor).
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDownload() {
    const result = await download.mutateAsync(transaction.id);
    // Abre numa aba nova — a URL já é assinada e aponta direto pro R2,
    // não passa pelo nosso backend de novo.
    window.open(result.download_url, "_blank", "noopener,noreferrer");
  }

  async function handleRemove() {
    if (!window.confirm("Remover o anexo deste lançamento?")) return;
    await remove.mutateAsync();
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">Comprovante (nota fiscal / cupom fiscal)</p>

      {transaction.attachment_filename ? (
        <div className="flex items-center justify-between rounded-md border border-border p-3">
          <div className="min-w-0">
            <p className="truncate text-sm">{transaction.attachment_filename}</p>
            {transaction.attachment_size_bytes !== null && (
              <p className="text-xs text-muted-foreground">{formatFileSize(transaction.attachment_size_bytes)}</p>
            )}
          </div>
          <div className="flex shrink-0 gap-2">
            <Button type="button" variant="outline" size="sm" onClick={handleDownload} disabled={download.isPending}>
              Baixar
            </Button>
            <Button type="button" variant="destructive" size="sm" onClick={handleRemove} disabled={remove.isPending}>
              Remover
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
            onChange={handleFileSelected}
            disabled={upload.isPending}
            className="block w-full text-sm text-muted-foreground file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-2 file:text-sm file:font-medium file:text-primary-foreground hover:file:opacity-90"
          />
          <p className="text-xs text-muted-foreground">JPEG, PNG ou PDF — até 10MB.</p>
          {upload.isPending && <p className="text-xs text-muted-foreground">Enviando...</p>}
          {uploadError && <p className="text-xs text-destructive">{uploadError}</p>}
        </div>
      )}
    </div>
  );
}
