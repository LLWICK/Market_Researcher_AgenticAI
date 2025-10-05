import { useState } from "react";
import { Search } from "lucide-react";

export default function QueryInput({ onSubmit }) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query);
      setQuery("");
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center space-x-2 p-4 bg-white rounded-2xl shadow"
    >
      <input
        type="text"
        placeholder="Ask about markets, competitors, or trends..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="flex-1 p-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        type="submit"
        className="flex items-center space-x-2 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition"
      >
        <Search className="w-5 h-5" />
        <span>Analyze</span>
      </button>
    </form>
  );
}
