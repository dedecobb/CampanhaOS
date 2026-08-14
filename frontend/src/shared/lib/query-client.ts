import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Não tenta de novo automaticamente em erro 401/403/404 — só faz
      // sentido re-tentar erros transitórios (rede, 500), não erros que
      // vão continuar dando o mesmo resultado até o usuário agir.
      retry: (failureCount, error) => {
        const status = (error as { response?: { status?: number } })?.response?.status;
        if (status && [401, 403, 404, 422].includes(status)) {
          return false;
        }
        return failureCount < 2;
      },
      // 30s: dado considerado "fresco" por meio minuto antes de
      // revalidar automaticamente ao focar a janela de novo — equilíbrio
      // entre não sobrecarregar a API e não mostrar dado desatualizado.
      staleTime: 30_000,
    },
  },
});
