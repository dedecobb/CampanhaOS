import { useState } from "react";
import { Link, Outlet } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { useAuth } from "@/features/auth/context/AuthContext";

const NAV_LINKS = [
  { to: "/", label: "Início" },
  { to: "/eleitores", label: "Eleitores" },
  { to: "/liderancas", label: "Lideranças" },
  { to: "/agenda", label: "Agenda" },
  { to: "/financeiro", label: "Financeiro" },
  { to: "/mapa", label: "Mapa" },
  { to: "/link-cadastro", label: "Link de Autocadastro" },
];

export function DashboardLayout() {
  const { user, logout } = useAuth();
  // Controla a "gaveta" do menu no celular — no computador (md e acima),
  // o CSS ignora esse estado e mantém o menu sempre visível e fixo.
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      {/* Fundo escurecido atrás do menu no celular — clicar nele fecha o menu.
          Só existe (renderiza) quando o menu está aberto, e "md:hidden"
          garante que nunca aparece no computador, mesmo se o estado
          ficasse true por engano. */}
      {isMobileNavOpen && (
        <button
          type="button"
          aria-label="Fechar menu"
          onClick={() => setIsMobileNavOpen(false)}
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 shrink-0 overflow-y-auto border-r border-border bg-background p-4 transition-transform duration-200 ease-in-out md:static md:z-auto md:w-56 md:translate-x-0 md:bg-muted/20 ${
          isMobileNavOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-6 flex items-center justify-between">
          <p className="text-lg font-semibold">CampanhaOS</p>
          <button
            type="button"
            onClick={() => setIsMobileNavOpen(false)}
            className="rounded-md p-1 hover:bg-accent md:hidden"
            aria-label="Fechar menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="space-y-1">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              onClick={() => setIsMobileNavOpen(false)}
              className="block rounded-md px-3 py-2 text-sm hover:bg-accent"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border px-4 py-3 md:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              onClick={() => setIsMobileNavOpen(true)}
              className="shrink-0 rounded-md p-2 hover:bg-accent md:hidden"
              aria-label="Abrir menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <span className="truncate text-sm text-muted-foreground">{user?.name}</span>
          </div>
          <Button variant="outline" size="sm" onClick={logout} className="shrink-0">
            Sair
          </Button>
        </header>

        <main className="flex-1 overflow-x-hidden p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
