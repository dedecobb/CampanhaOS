import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";

/**
 * Envolve rotas que exigem usuário autenticado. Enquanto o bootstrap da
 * sessão (AuthContext) ainda está rodando, mostra um estado de
 * carregamento em vez de redirecionar precocemente para o login — sem
 * isso, um F5 na página sempre mandaria o usuário de volta ao login por
 * uma fração de segundo, mesmo com uma sessão válida salva.
 */
export function ProtectedRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Carregando...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
