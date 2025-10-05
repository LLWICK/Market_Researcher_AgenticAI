import React from "react";

const EventSpikesTable = ({ events }) => (
  <div className="bg-white shadow rounded-2xl p-5 col-span-2 border border-gray-100">
    <h2 className="text-lg font-semibold mb-3 text-gray-800">
      Recent Market Events
    </h2>
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="p-2">Date</th>
            <th className="p-2">Company</th>
            <th className="p-2">Direction</th>
            <th className="p-2">% Move (1D)</th>
            <th className="p-2">Headline</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e, idx) => (
            <tr key={idx} className="border-t">
              <td className="p-2">{e.date}</td>
              <td className="p-2">{e.entity_or_topic}</td>
              <td
                className={`p-2 font-semibold ${
                  e.direction === "+" ? "text-green-600" : "text-red-600"
                }`}
              >
                {e.direction === "+" ? "▲" : "▼"}
              </td>
              <td className="p-2">{e.price_move_1d_pct}%</td>
              <td className="p-2">{e.headline}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

export default EventSpikesTable;
