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

const MarketTrendChart = ({ sectorPerformance }) => {
  if (!sectorPerformance || !sectorPerformance.series || !sectorPerformance.x) {
    return (
      <div className="bg-white shadow rounded-2xl p-5 col-span-2 border border-gray-100 text-gray-500 text-center">
        Loading Market Trends...
      </div>
    );
  }

  // Safely map chart data
  const chartData = sectorPerformance.x.map((x, i) => ({
    year: x,
    Product: sectorPerformance.series[0]?.data[i] ?? null,
    Sector: sectorPerformance.series[1]?.data[i] ?? null,
  }));

  return (
    <div className="bg-white shadow rounded-2xl p-5 col-span-2 border border-gray-100">
      <h2 className="text-lg font-semibold mb-4 text-gray-800">
        {sectorPerformance.title || "Market Trends"}
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="Product" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="Sector" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MarketTrendChart;
