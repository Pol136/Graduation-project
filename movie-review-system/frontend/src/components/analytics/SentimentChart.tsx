import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { sentimentLabel } from "../../utils/labels";

interface SentimentChartProps {
  distribution: Record<string, number>;
}

export default function SentimentChart({ distribution }: SentimentChartProps) {
  const data = Object.entries(distribution).map(([key, value]) => ({
    name: sentimentLabel(key),
    count: value,
  }));

  if (data.every((d) => d.count === 0)) {
    return null;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
        <Tooltip />
        <Bar dataKey="count" fill="#2563eb" name="Количество" />
      </BarChart>
    </ResponsiveContainer>
  );
}
