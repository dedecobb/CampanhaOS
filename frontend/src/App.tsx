import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";
import { AuthProvider } from "@/features/auth/context/AuthContext";
import { queryClient } from "@/shared/lib/query-client";
import { router } from "@/routes/router";

/**
 * Bloco C: adiciona o AuthProvider, envolvendo o roteamento — assim
 * qualquer rota (incluindo o ProtectedRoute) tem acesso ao estado de
 * autenticação via useAuth().
 */
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
