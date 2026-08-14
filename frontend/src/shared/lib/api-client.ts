import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

/**
 * Formato de erro que nosso backend retorna (ver
 * backend/src/presentation/api/error_handlers.py) — todo erro da API tem
 * um campo `detail`, seja violação de regra de negócio (DomainError) seja
 * erro de caso de uso (ApplicationError).
 */
export interface ApiErrorResponse {
  detail: string;
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
    return axiosError.response?.data?.detail ?? "Erro de comunicação com o servidor. Tente novamente.";
  }
  return "Erro inesperado. Tente novamente.";
}
