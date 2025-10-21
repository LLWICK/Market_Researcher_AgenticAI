import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp } from "lucide-react";

export default function TrendChart({ data }) {
  // Example fallback
  const exampleData = [
    { name: "Palo Alto", value: 120 },
    { name: "Zscaler", value: 95 },
    { name: "Fortinet", value: 88 },
    { name: "Cisco", value: 70 },
    { name: "Check Point", value: 55 },
  ];

  const chartData = data || exampleData;

  return (
    <div className="p-4 bg-white rounded-2xl shadow h-80">
      <div className="flex items-center space-x-2 mb-4">
        <TrendingUp className="w-5 h-5 text-green-500" />
        <h2 className="text-lg font-semibold">Top Competitors</h2>
      </div>

      <ResponsiveContainer width="100%" height="90%">
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#3b82f6" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
