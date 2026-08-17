import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { GENDER_COLORS, GENDER_LABELS, type DashboardStats } from "@/features/dashboard/api/types";

interface GenderPieChartProps {
  genderBreakdown: DashboardStats["gender_breakdown"];
}

export function GenderPieChart({ genderBreakdown }: GenderPieChartProps) {
  const data = Object.entries(genderBreakdown)
    .filter(([, count]) => count > 0)
    .map(([key, count]) => ({
      key,
      name: GENDER_LABELS[key] ?? key,
      value: count,
    }));

  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">Nenhum dado de gênero cadastrado ainda.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
          {data.map((entry) => (
            <Cell key={entry.key} fill={GENDER_COLORS[entry.key] ?? "#9ca3af"} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
