import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const CompetitorTrendChart = ({ timeseries }) => {
  const chartData = timeseries.x.map((x, i) => {
    const row = { year: x };
    timeseries.series.forEach((s) => (row[s.name] = s.data[i]));
    return row;
  });

  return (
    <div className="bg-white shadow rounded-2xl p-5 col-span-2 border border-gray-100">
      <h2 className="text-lg font-semibold mb-4 text-gray-800">
        {timeseries.title}
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis />
          <Tooltip />
          <Legend />
          {timeseries.series.map((s, idx) => (
            <Line
              key={idx}
              type="monotone"
              dataKey={s.name}
              strokeWidth={2}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CompetitorTrendChart;
