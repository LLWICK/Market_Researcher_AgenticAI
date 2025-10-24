import React, { useState, useEffect } from "react";
import axios from "axios";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { Loader2, Trash2, Upload, FileText } from "lucide-react";

const RagDocs2 = ({ userId }) => {
  const [docs, setDocs] = useState([]);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchDocs = async () => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/rag/documents`, {
        params: { user_id: userId },
      });
      setDocs(res.data.documents || []);
    } catch (err) {
      toast.error("Failed to load documents.");
    }
  };

  useEffect(() => {
    if (userId) fetchDocs();
  }, [userId]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return toast.warning("Please select a file first.");
    setLoading(true);

    const formData = new FormData();
    formData.append("user_id", userId);
    formData.append("file", file);

    try {
      await axios.post(`http://127.0.0.1:8000/upload-document`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Document uploaded successfully!");
      setFile(null);
      fetchDocs();
    } catch (err) {
      toast.error("Upload failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (docId) => {
    setLoading(true);
    try {
      await axios.delete(
        `http://127.0.0.1:8000/rag/delete-document/${userId}/${docId}`
      );
      toast.success("Document deleted successfully!");
      fetchDocs();
    } catch (err) {
      toast.error("Failed to delete document.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-5 bg-white rounded-2xl shadow-md border border-gray-200">
      <ToastContainer position="top-right" autoClose={2000} theme="colored" />

      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <FileText className="w-5 h-5 text-blue-600" />
        Your RAG Documents
      </h2>

      {/* Upload Section */}
      <form
        onSubmit={handleUpload}
        className="flex items-center gap-3 mb-4 border border-gray-300 rounded-xl p-3 bg-gray-50"
      >
        <input
          type="file"
          onChange={(e) => setFile(e.target.files[0])}
          className="flex-1 text-sm"
        />
        <button
          type="submit"
          disabled={loading}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-all"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Upload className="w-4 h-4" />
          )}
          Upload
        </button>
      </form>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200">
        <table className="w-full text-sm text-gray-700">
          <thead className="bg-gray-100">
            <tr>
              <th className="text-left px-4 py-2 border-b">Document ID</th>
              <th className="text-left px-4 py-2 border-b">Filename</th>
              <th className="px-4 py-2 border-b text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {docs.length > 0 ? (
              docs.map((doc) => (
                <tr
                  key={doc.id}
                  className="hover:bg-gray-50 transition-colors duration-150"
                >
                  <td className="px-4 py-2 border-b">{doc.id}</td>
                  <td className="px-4 py-2 border-b">
                    {doc.metadata?.filename || "N/A"}
                  </td>
                  <td className="px-4 py-2 border-b text-center">
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="text-red-500 hover:text-red-700 transition-colors"
                      disabled={loading}
                    >
                      {loading ? (
                        <Loader2 className="w-4 h-4 animate-spin inline-block" />
                      ) : (
                        <Trash2 className="w-4 h-4 inline-block" />
                      )}
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan="3"
                  className="text-center text-gray-500 py-4 border-t"
                >
                  No documents uploaded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RagDocs2;
