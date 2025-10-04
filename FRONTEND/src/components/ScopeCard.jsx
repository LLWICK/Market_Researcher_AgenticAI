import { Code2 } from "lucide-react";

export default function ScopeCard(prop) {
  // Example fallback data

  return (
    <div className="p-4 bg-white rounded-2xl shadow space-y-2">
      <div className="flex items-center space-x-2 mb-2">
        <Code2 className="w-5 h-5 text-blue-500" />
        <h2 className="text-lg font-semibold">{prop.title}</h2>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="font-semibold">Scale:</span> {prop.scale}
        </div>
        <div>
          <span className="font-semibold">Sector:</span> {prop.sector}
        </div>
        <div>
          <span className="font-semibold">Time Range:</span> {prop.timeRange}
        </div>
        <div className="col-span-2">
          <span className="font-semibold">Competitors:</span>{" "}
        </div>
      </div>
    </div>
  );
}
