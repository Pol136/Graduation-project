import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface AspectScoresChartProps {
  aspectScores: Record<string, number>;
}

export default function AspectScoresChart({ aspectScores }: AspectScoresChartProps) {
  const data = Object.entries(aspectScores)
    .map(([aspect, score]) => ({ aspect, score }))
    .sort((a, b) => b.score - a.score);

  if (data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, data.length * 28)}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 8, right: 16, left: 8, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 12 }} />
        <YAxis
          type="category"
          dataKey="aspect"
          width={140}
          tick={{ fontSize: 11 }}
        />
        <Tooltip formatter={(v: number) => v.toFixed(2)} />
        <Bar dataKey="score" fill="#16a34a" name="Оценка" />
      </BarChart>
    </ResponsiveContainer>
  );
}
