import React from "react";

const MarketInsightsCard = ({ insights }) => (
  <div className="bg-white shadow rounded-2xl p-5 border border-gray-100">
    <h2 className="text-lg font-semibold mb-2 text-gray-800">
      Market Insights
    </h2>
    <p className="text-gray-700 whitespace-pre-line text-sm">{insights}</p>
  </div>
);

export default MarketInsightsCard;
