import { useEffect, useState } from "react";
import axios from "axios";
import SideBar from "../components/SideBar";
import QueryInput from "../components/QueryInput";
import ScopeCard from "../components/ScopeCard";
import MarketInsightsCard from "../components/MarketInsightsCard";
import SocialTrendsCard from "../components/SocialTrendsCard";
import CompetitorTrendChart from "../components/CompetitorTrendChart";
import MarketTrendChart from "../components/MarketTrendChart";
import EventSpikesTable from "../components/EventSpikesTable";
import ChatHistory from "../components/ChatHistory";
import { jwtDecode } from "jwt-decode";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [trigger, setTrigger] = useState(false);
  const [userId, setUserId] = useState(null); // replace with logged-in user ID

  useEffect(() => {
    const token = localStorage.getItem("token");
    const decoded = jwtDecode(token);
    setUserId(decoded.user_id);
  }, []);

  const handleQuerySubmit = (query) => {
    axios
      .post("http://127.0.0.1:8000/analyze", { query })
      .then((res) => {
        setData(res.data.team_b);
        setTrigger(true);

        // Save query + response
        axios.post("http://127.0.0.1:8000/save_chat", {
          user_id: userId,
          query,
          response: res.data.team_b,
        });
      })
      .catch(console.error);
  };

  const handleSelectQuery = (item) => {
    setData(item.response);
    setTrigger(true);
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      <SideBar />
      <div className="flex-1 p-6 grid grid-cols-3 gap-6">
        <div className="col-span-1">
          <ChatHistory userId={userId} onSelectQuery={handleSelectQuery} />
        </div>

        <main className="col-span-2 space-y-6">
          <QueryInput onSubmit={handleQuerySubmit} />
          {trigger && data && (
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
              <EventSpikesTable events={data.event_spikes?.events_detected} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
