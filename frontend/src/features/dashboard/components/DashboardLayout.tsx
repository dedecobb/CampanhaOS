import { Link, Outlet } from "react-router-dom";
import { Button } from "@/shared/components/ui/button";
import { useAuth } from "@/features/auth/context/AuthContext";

export function DashboardLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r border-border bg-muted/20 p-4">
        <p className="mb-6 text-lg font-semibold">CampanhaOS</p>
        <nav className="space-y-1">
          <Link to="/" className="block rounded-md px-3 py-2 text-sm hover:bg-accent">
            Início
          </Link>
          <Link to="/eleitores" className="block rounded-md px-3 py-2 text-sm hover:bg-accent">
            Eleitores
          </Link>
          <Link to="/liderancas" className="block rounded-md px-3 py-2 text-sm hover:bg-accent">
            Lideranças
          </Link>
          <Link to="/agenda" className="block rounded-md px-3 py-2 text-sm hover:bg-accent">
            Agenda
          </Link>
          <Link to="/financeiro" className="block rounded-md px-3 py-2 text-sm hover:bg-accent">
            Financeiro
          </Link>
          <Link to="/mapa" className="block rounded-md px-3 py-2 text-sm hover:bg-accent">
            Mapa
          </Link>
          <Link to="/link-cadastro" className="block rounded-md px-3 py-2 text-sm hover:bg-accent">
            Link de Autocadastro
          </Link>
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border px-6 py-3">
          <span className="text-sm text-muted-foreground">{user?.name}</span>
          <Button variant="outline" size="sm" onClick={logout}>
            Sair
          </Button>
        </header>

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
