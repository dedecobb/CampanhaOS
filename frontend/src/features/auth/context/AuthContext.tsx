import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { getCurrentUser, login as loginRequest, refreshToken as refreshTokenRequest } from "@/features/auth/api/auth-api";
import type { UserMeResponse } from "@/features/auth/api/types";
import { setAuthRefreshHandler, setAuthTokenGetter } from "@/shared/lib/api-client";

const REFRESH_TOKEN_STORAGE_KEY = "campanhaos:refresh_token";

interface AuthContextValue {
  user: UserMeResponse | null;
  /** true enquanto tenta restaurar a sessão a partir do refresh token salvo (bootstrap inicial). */
  isLoading: boolean;
  login: (tenantId: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserMeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Ref (não state) para o access token: o interceptor do axios precisa
  // de uma função SÍNCRONA que sempre leia o valor mais atual — se
  // usássemos state diretamente numa closure capturada uma única vez no
  // useEffect de setup, ficaríamos presos ao valor do momento em que o
  // efeito rodou (stale closure), não ao valor atual depois de um login.
  const accessTokenRef = useRef<string | null>(null);

  const applyTokens = useCallback((accessToken: string, refreshTokenValue: string) => {
    accessTokenRef.current = accessToken;
    sessionStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refreshTokenValue);
  }, []);

  const clearSession = useCallback(() => {
    accessTokenRef.current = null;
    sessionStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
    setUser(null);
  }, []);

  const attemptRefresh = useCallback(async (): Promise<boolean> => {
    const savedRefreshToken = sessionStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
    if (!savedRefreshToken) {
      return false;
    }
    try {
      const tokens = await refreshTokenRequest({ refresh_token: savedRefreshToken });
      applyTokens(tokens.access_token, tokens.refresh_token);
      return true;
    } catch {
      clearSession();
      return false;
    }
  }, [applyTokens, clearSession]);

  // Conecta os pontos de extensão do cliente HTTP uma única vez.
  useEffect(() => {
    setAuthTokenGetter(() => accessTokenRef.current);
    setAuthRefreshHandler(attemptRefresh);
  }, [attemptRefresh]);

  // Bootstrap: ao carregar a página, tenta restaurar a sessão a partir
  // do refresh token salvo no sessionStorage (sobrevive a um F5).
  useEffect(() => {
    async function bootstrap() {
      const refreshed = await attemptRefresh();
      if (refreshed) {
        try {
          const me = await getCurrentUser();
          setUser(me);
        } catch {
          clearSession();
        }
      }
      setIsLoading(false);
    }
    void bootstrap();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(async (tenantId: string, email: string, password: string) => {
    const tokens = await loginRequest({ tenant_id: tenantId, email, password });
    applyTokens(tokens.access_token, tokens.refresh_token);
    const me = await getCurrentUser();
    setUser(me);
  }, [applyTokens]);

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth precisa ser usado dentro de um <AuthProvider>");
  }
  return context;
}
