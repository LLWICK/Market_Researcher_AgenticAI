import React from "react";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";

const SocialTrendsCard = ({ trends }) => (
  <div className="bg-white shadow rounded-2xl p-5 border border-gray-100">
    <h2 className="text-lg font-semibold mb-4 text-gray-800">Social Trends</h2>
    <div className="space-y-2 max-h-80 overflow-y-auto">
      {trends.map((t, idx) => (
        <div
          key={idx}
          className={`p-2 rounded-lg flex justify-between items-center ${
            t.sentiment === "positive"
              ? "bg-green-50 border border-green-200"
              : t.sentiment === "negative"
              ? "bg-red-50 border border-red-200"
              : "bg-gray-50 border border-gray-200"
          }`}
        >
          <span className="text-sm">{t.trend}</span>
          {t.sentiment === "positive" ? (
            <TrendingUp className="text-green-600" size={18} />
          ) : t.sentiment === "negative" ? (
            <TrendingDown className="text-red-600" size={18} />
          ) : (
            <Activity className="text-gray-500" size={18} />
          )}
        </div>
      ))}
    </div>
  </div>
);

export default SocialTrendsCard;
