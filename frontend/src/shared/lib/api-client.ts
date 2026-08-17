import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

/**
 * Formato de erro que nosso backend retorna. Tem DUAS formas possíveis:
 *
 * 1. Erro de regra de negócio (DomainError/ApplicationError, mapeado por
 *    error_handlers.py) -> `detail` é uma STRING simples.
 * 2. Erro de validação automática do FastAPI (422 — corpo da requisição
 *    não bate com o schema Pydantic, gerado ANTES de qualquer código
 *    nosso rodar) -> `detail` é uma LISTA de objetos, um por campo
 *    inválido, formato `{loc, msg, type}`.
 *
 * Tratar só o caso 1 (como o tipo antigo assumia) faz o caso 2 aparecer
 * quebrado na tela (`[object Object]`) ou simplesmente não aparecer nada.
 */
export interface PydanticFieldError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ApiErrorResponse {
  detail: string | PydanticFieldError[];
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Ponto de extensão para o Bloco C conectar o access token.
 *
 * Por que não fazemos isso direto aqui: o token vive no estado do
 * AuthContext (React), não neste módulo — este arquivo é carregado antes
 * de qualquer componente React existir, então não pode importar o
 * contexto diretamente sem criar uma dependência circular. Em vez disso,
 * o AuthProvider vai chamar `setAuthTokenGetter` uma vez, na
 * inicialização, passando uma função que sempre retorna o token atual.
 */
let getAuthToken: (() => string | null) | null = null;

export function setAuthTokenGetter(getter: () => string | null): void {
  getAuthToken = getter;
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAuthToken?.();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Mesmo padrão de `setAuthTokenGetter`: o AuthProvider registra uma
 * função que tenta renovar o token (chamando POST /auth/refresh) e
 * retorna `true`/`false` conforme o sucesso. Usado pelo interceptor de
 * resposta abaixo.
 */
let refreshHandler: (() => Promise<boolean>) | null = null;

export function setAuthRefreshHandler(handler: () => Promise<boolean>): void {
  refreshHandler = handler;
}

// Evita múltiplas chamadas de refresh simultâneas se várias requisições
// falharem com 401 ao mesmo tempo (ex: a página carrega e dispara 3
// requisições em paralelo, todas com token expirado) — todas esperam a
// MESMA promise de refresh, em vez de disparar 3 refreshes concorrentes.
let ongoingRefresh: Promise<boolean> | null = null;

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;

    const isAuthEndpoint = originalRequest?.url?.includes("/auth/login") || originalRequest?.url?.includes("/auth/refresh");

    if (error.response?.status !== 401 || !originalRequest || originalRequest._retried || isAuthEndpoint || !refreshHandler) {
      return Promise.reject(error);
    }

    originalRequest._retried = true;

    if (!ongoingRefresh) {
      ongoingRefresh = refreshHandler().finally(() => {
        ongoingRefresh = null;
      });
    }

    const refreshed = await ongoingRefresh;
    if (!refreshed) {
      return Promise.reject(error);
    }

    // Repete a requisição original — o interceptor de request (acima) já
    // vai anexar o novo access token automaticamente.
    return apiClient(originalRequest);
  },
);

/**
 * Extrai a mensagem de erro do backend de forma segura, com um fallback
 * genérico para erros de rede/timeout que não têm o formato esperado.
 */
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorResponse>;
    const detail = axiosError.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      // Erro de validação automática do FastAPI (422) — monta uma
      // mensagem legível a partir da lista de campos inválidos, em vez
      // de deixar a lista "crua" chegar na tela.
      return detail
        .map((fieldError) => {
          const fieldName = fieldError.loc[fieldError.loc.length - 1] ?? "campo";
          return `${fieldName}: ${fieldError.msg}`;
        })
        .join(" | ");
    }

    return "Erro de comunicação com o servidor. Tente novamente.";
  }
  return "Erro inesperado. Tente novamente.";
}
