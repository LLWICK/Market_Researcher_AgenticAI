import { useEffect, useState } from "react";
import axios from "axios";
import { Trash2 } from "lucide-react"; // optional: icon library (shadcn/lucide)

export default function ChatHistory({ userId, onSelectQuery }) {
  const [history, setHistory] = useState([]);

  const fetchHistory = async () => {
    if (userId) {
      try {
        const res = await axios.get(
          `http://127.0.0.1:8000/get_chats/${userId}`
        );
        setHistory(res.data.history);
      } catch (err) {
        console.error("Error fetching chat history:", err);
      }
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [userId]);

  const handleDelete = async (chatId) => {
    if (!window.confirm("Are you sure you want to delete this chat?")) return;
    try {
      await axios.delete(`http://127.0.0.1:8000/delete_chat/${chatId}`);
      setHistory((prev) => prev.filter((chat) => chat._id !== chatId));
    } catch (err) {
      console.error("Error deleting chat:", err);
      alert("Failed to delete chat");
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow p-4 h-[80vh] overflow-y-auto">
      <h2 className="text-xl font-semibold mb-3 flex justify-between items-center">
        Chat History
        <button
          onClick={fetchHistory}
          className="text-sm text-indigo-500 hover:underline"
        >
          Refresh
        </button>
      </h2>

      {history.length === 0 ? (
        <p className="text-gray-500 text-sm">No chats yet</p>
      ) : (
        <ul className="space-y-3">
          {history.map((item) => (
            <li
              key={item._id}
              className="flex justify-between items-center p-3 border border-gray-200 rounded-xl hover:bg-indigo-50 transition"
            >
              <div
                onClick={() => onSelectQuery(item)}
                className="flex-1 cursor-pointer"
              >
                <p className="font-medium text-gray-800 truncate">
                  {item.query}
                </p>
                <p className="text-sm text-gray-500">
                  {item.timestamp
                    ? new Date(item.timestamp).toLocaleString()
                    : ""}
                </p>
              </div>

              {/* 🗑 Delete button */}
              <button
                onClick={() => handleDelete(item._id)}
                className="ml-3 text-red-500 hover:text-red-700 transition"
                title="Delete chat"
              >
                <Trash2 size={18} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
