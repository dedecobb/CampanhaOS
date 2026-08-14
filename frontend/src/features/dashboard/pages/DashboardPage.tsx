import { useAuth } from "@/features/auth/context/AuthContext";

/**
 * MVP: só uma saudação. Dashboard com métricas/gráficos de verdade
 * (RF-03 da Fase 1) é escopo de um módulo futuro, não deste — este
 * módulo só precisava provar que login + navegação protegida funcionam.
 */
export function DashboardPage() {
  const { user } = useAuth();

  return (
    <div>
      <h1 className="text-2xl font-semibold">Olá, {user?.name}</h1>
      <p className="mt-2 text-muted-foreground">Bem-vindo ao CampanhaOS.</p>
    </div>
  );
}
