import { useState, useEffect } from "react";
import axios from "axios";

export default function RagDocuments({ userId }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchDocs = async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const res = await axios.get(
        `http://127.0.0.1:8000/rag/documents?user_id=${userId}`
      );
      setDocs(res.data.documents);
    } catch (err) {
      console.error("Error fetching docs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, [userId]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !userId) return;

    const formData = new FormData();
    formData.append("user_id", userId);
    formData.append("file", file);

    try {
      await axios.post("http://127.0.0.1:8000/upload-document", formData);
      fetchDocs();
    } catch (err) {
      console.error("Upload failed:", err);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-lg font-semibold mb-3">Your RAG Documents</h2>

      <div className="flex items-center gap-3 mb-4">
        <input
          type="file"
          onChange={handleFileUpload}
          className="border p-2 rounded"
        />
        <button
          onClick={fetchDocs}
          className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <p>Loading documents...</p>
      ) : docs.length > 0 ? (
        <ul className="space-y-2">
          {docs.map((d) => (
            <li
              key={d.id}
              className="p-2 bg-gray-50 border rounded flex justify-between items-center"
            >
              <span>{d.metadata?.filename || d.id}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-gray-500">No documents uploaded yet.</p>
      )}
    </div>
  );
}
