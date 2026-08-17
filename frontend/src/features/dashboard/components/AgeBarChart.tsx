import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AGE_BRACKET_LABELS, AGE_BRACKET_ORDER, type DashboardStats } from "@/features/dashboard/api/types";

interface AgeBarChartProps {
  ageBreakdown: DashboardStats["age_breakdown"];
}

export function AgeBarChart({ ageBreakdown }: AgeBarChartProps) {
  // Ordem fixa (AGE_BRACKET_ORDER), não a ordem que veio da API — o
  // backend agrupa via SQL GROUP BY, que não garante nenhuma ordem
  // específica de retorno.
  const data = AGE_BRACKET_ORDER.filter((bracket) => (ageBreakdown[bracket] ?? 0) > 0).map((bracket) => ({
    bracket: AGE_BRACKET_LABELS[bracket] ?? bracket,
    quantidade: ageBreakdown[bracket] ?? 0,
  }));

  if (data.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        Nenhum dado de data de nascimento cadastrado ainda.
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="bracket" fontSize={12} />
        <YAxis allowDecimals={false} fontSize={12} />
        <Tooltip />
        <Bar dataKey="quantidade" fill="#3b82f6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
