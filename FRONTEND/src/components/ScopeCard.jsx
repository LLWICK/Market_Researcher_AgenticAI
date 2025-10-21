import { Code2 } from "lucide-react";
import React from "react";

const ScopeCard = ({ summary }) => (
  <div className="bg-white shadow rounded-2xl p-5 col-span-2 border border-gray-100">
    <h2 className="text-xl font-semibold mb-2 text-gray-800">
      Executive Summary
    </h2>
    <p className="text-gray-700 whitespace-pre-line text-sm">{summary}</p>
  </div>
);

export default ScopeCard;
