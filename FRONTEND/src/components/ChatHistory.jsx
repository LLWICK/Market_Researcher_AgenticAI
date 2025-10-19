import { useEffect, useState } from "react";
import axios from "axios";

export default function ChatHistory({ userId, onSelectQuery }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (userId) {
      axios
        .get(`http://127.0.0.1:8000/get_chats/${userId}`)
        .then((res) => setHistory(res.data.history))
        .catch((err) => console.error("Error fetching chat history:", err));
    }
  }, [userId]);

  return (
    <div className="bg-white rounded-2xl shadow p-4 h-[80vh] overflow-y-auto">
      <h2 className="text-xl font-semibold mb-3">Chat History</h2>
      {history.length === 0 ? (
        <p className="text-gray-500 text-sm">No chats yet</p>
      ) : (
        <ul className="space-y-3">
          {history.map((item) => (
            <li
              key={item._id}
              onClick={() => onSelectQuery(item)}
              className="p-3 border border-gray-200 rounded-xl hover:bg-indigo-50 cursor-pointer transition"
            >
              <p className="font-medium text-gray-800 truncate">{item.query}</p>
              <p className="text-sm text-gray-500">
                {new Date(item.timestamp).toLocaleString()}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
