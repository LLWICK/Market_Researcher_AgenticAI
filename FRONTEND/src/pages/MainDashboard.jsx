import { useEffect, useState } from "react";
import axios from "axios";
import { jwtDecode } from "jwt-decode";
import { ClipLoader } from "react-spinners";
import SideBar from "../components/SideBar";
import QueryInput from "../components/QueryInput";
import ScopeCard from "../components/ScopeCard";
import MarketInsightsCard from "../components/MarketInsightsCard";
import SocialTrendsCard from "../components/SocialTrendsCard";
import CompetitorTrendChart from "../components/CompetitorTrendChart";
import MarketTrendChart from "../components/MarketTrendChart";
import EventSpikesTable from "../components/EventSpikesTable";
import ChatHistory from "../components/ChatHistory";
import RagDocuments from "../components/RagDocuments";
import RagResponseCard from "../components/RagResponseCard";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [trigger, setTrigger] = useState(false);
  const [userId, setUserId] = useState(null);
  const [useRag, setUseRag] = useState(false); // ✅ Toggle for RAG agent
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      const decoded = jwtDecode(token);
      setUserId(decoded.user_id);
    }
  }, []);

  const handleQuerySubmit = async (query) => {
    try {
      setLoading(true); // 🔹 Show loader

      if (!useRag) {
        // 🔹 Default IR Scraper pipeline
        const res = await axios.post("http://127.0.0.1:8000/analyze", {
          query,
        });
        setData(res.data.team_b);
        setTrigger(true);

        await axios.post("http://127.0.0.1:8000/save_chat", {
          user_id: userId,
          query,
          response: res.data.team_b,
        });
      } else {
        // 🔹 Use RAG Agent
        const formData = new FormData();
        formData.append("user_id", userId);
        formData.append("query", query);

        const res = await axios.post(
          "http://127.0.0.1:8000/rag/query",
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" },
          }
        );

        setData({ summary: res.data.response });
        setTrigger(true);

        await axios.post("http://127.0.0.1:8000/save_chat", {
          user_id: userId,
          query,
          response: res.data.response,
        });
      }
    } catch (err) {
      console.error("Query failed:", err);
    } finally {
      setLoading(false); // 🔹 Hide loader
    }
  };

  const handleSelectQuery = (item) => {
    setData(item.response);
    setTrigger(true);
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      <SideBar />
      <div className="flex-1 p-6 grid grid-cols-3 gap-6">
        {/* Left column: Chat history */}
        <div className="col-span-1 space-y-4">
          <ChatHistory userId={userId} onSelectQuery={handleSelectQuery} />

          {/* ✅ Show RAG documents if RAG mode is enabled */}
          {useRag && <RagDocuments userId={userId} />}
        </div>

        {/* Main content */}
        <main className="col-span-2 space-y-6">
          <div className="flex justify-between items-center mb-2">
            {/* ✅ RAG toggle */}
            <label className="flex items-center space-x-2">
              <span>Use RAG Agent</span>
              <input
                type="checkbox"
                checked={useRag}
                onChange={(e) => setUseRag(e.target.checked)}
              />
            </label>
          </div>

          <QueryInput onSubmit={handleQuerySubmit} />

          {loading ? (
            <div className="flex justify-center items-center h-64">
              <ClipLoader color="#3B82F6" size={50} />
              <p className="ml-3 text-gray-600 font-medium">
                Generating response...
              </p>
            </div>
          ) : (
            trigger &&
            data && (
              <>
                {useRag ? (
                  <RagResponseCard response={data.summary} />
                ) : (
                  <div className="grid grid-cols-2 gap-6">
                    <ScopeCard summary={data.summary} />
                    <MarketInsightsCard insights={data.market_insights} />
                    <SocialTrendsCard trends={data.social_trends} />
                    <CompetitorTrendChart
                      timeseries={data.competitor_trend?.timeseries}
                    />
                    <MarketTrendChart
                      sectorPerformance={data.market_trend?.sector_performance}
                    />
                    <EventSpikesTable
                      events={data.event_spikes?.events_detected}
                    />
                  </div>
                )}
              </>
            )
          )}
        </main>
      </div>
    </div>
  );
}
