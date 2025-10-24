export default function RagResponseCard({ response }) {
  return (
    <div className="bg-white shadow-md rounded-2xl p-6 border border-gray-200">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">
        🧠 RAG Agent Response
      </h2>
      <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
        {response || "No response available."}
      </p>
    </div>
  );
}
