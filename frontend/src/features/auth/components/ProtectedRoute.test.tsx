import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { useAuth } from "@/features/auth/context/AuthContext";

// Mocka o módulo inteiro do contexto — cada teste controla diretamente o
// que `useAuth()` retorna, sem precisar montar um AuthProvider real com
// chamadas de API de verdade por trás.
vi.mock("@/features/auth/context/AuthContext", () => ({
  useAuth: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuth);

function renderProtectedRoute() {
  return render(
    <MemoryRouter initialEntries={["/dashboard"]}>
      <Routes>
        <Route path="/login" element={<p>Página de login</p>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<p>Conteúdo protegido</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  it("mostra estado de carregamento enquanto a sessão está sendo restaurada", () => {
    mockedUseAuth.mockReturnValue({ user: null, isLoading: true, login: vi.fn(), logout: vi.fn() });

    renderProtectedRoute();

    expect(screen.getByText("Carregando...")).toBeInTheDocument();
    expect(screen.queryByText("Conteúdo protegido")).not.toBeInTheDocument();
  });

  it("redireciona para /login quando não há usuário autenticado", () => {
    mockedUseAuth.mockReturnValue({ user: null, isLoading: false, login: vi.fn(), logout: vi.fn() });

    renderProtectedRoute();

    expect(screen.getByText("Página de login")).toBeInTheDocument();
    expect(screen.queryByText("Conteúdo protegido")).not.toBeInTheDocument();
  });

  it("renderiza o conteúdo protegido quando o usuário está autenticado", () => {
    mockedUseAuth.mockReturnValue({
      user: { id: "1", tenant_id: "t1", name: "Deco", email: "deco@teste.dev", role_names: [] },
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderProtectedRoute();

    expect(screen.getByText("Conteúdo protegido")).toBeInTheDocument();
    expect(screen.queryByText("Página de login")).not.toBeInTheDocument();
  });
});
