import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DashboardStats } from "@/features/dashboard/api/types";

interface RegistrationGrowthChartProps {
  registrationGrowth: DashboardStats["registration_growth"];
}

/**
 * O backend só retorna dias que TIVERAM cadastro (GROUP BY não inclui
 * dias vazios) — preenchemos os dias sem cadastro com 0 aqui, senão o
 * gráfico de linha ficaria com "buracos" enganosos em vez de mostrar
 * claramente os dias parados.
 */
function fillLast30Days(points: DashboardStats["registration_growth"]): { day: string; quantidade: number }[] {
  // Mesma proteção defensiva das outras — evita quebrar a página
  // inteira se esse campo vier undefined.
  const countByDay = new Map((points ?? []).map((p) => [p.day, p.count]));
  const result: { day: string; quantidade: number }[] = [];

  for (let i = 29; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const isoDay = date.toISOString().split("T")[0];
    const shortLabel = date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
    result.push({ day: shortLabel, quantidade: countByDay.get(isoDay) ?? 0 });
  }

  return result;
}

export function RegistrationGrowthChart({ registrationGrowth }: RegistrationGrowthChartProps) {
  const data = fillLast30Days(registrationGrowth);
  const hasAnyData = data.some((d) => d.quantidade > 0);

  if (!hasAnyData) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">Nenhum cadastro nos últimos 30 dias ainda.</p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="day" fontSize={11} interval={4} />
        <YAxis allowDecimals={false} fontSize={12} />
        <Tooltip />
        <Line type="monotone" dataKey="quantidade" stroke="#3b82f6" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
