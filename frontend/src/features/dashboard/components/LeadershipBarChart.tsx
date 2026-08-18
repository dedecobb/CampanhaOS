import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DashboardStats } from "@/features/dashboard/api/types";

interface LeadershipBarChartProps {
  leadershipBreakdown: DashboardStats["leadership_breakdown"];
}

export function LeadershipBarChart({ leadershipBreakdown }: LeadershipBarChartProps) {
  const data = leadershipBreakdown
    .filter((point) => point.count > 0)
    .map((point) => ({ name: point.leadership_name, quantidade: point.count }));

  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">Nenhum eleitor cadastrado ainda.</p>;
  }

  // Altura cresce com a quantidade de lideranças — barra horizontal
  // precisa de mais espaço vertical conforme a lista cresce, diferente
  // de um gráfico de barras verticais (que cresce pra largura).
  const chartHeight = Math.max(120, data.length * 40);

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart data={data} layout="vertical" margin={{ left: 24 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" allowDecimals={false} fontSize={12} />
        <YAxis type="category" dataKey="name" width={120} fontSize={12} />
        <Tooltip />
        <Bar dataKey="quantidade" fill="#3b82f6" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
