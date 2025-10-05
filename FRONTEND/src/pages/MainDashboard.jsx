import SideBar from "../components/SideBar";
import QueryInput from "../components/QueryInput";
import ScopeCard from "../components/ScopeCard";
import TrendChart from "../components/TrendChart";
import axios from "axios";
import { useState } from "react";
import MarketInsightsCard from "../components/MarketInsightsCard";
import SocialTrendsCard from "../components/SocialTrendsCard";
import EventSpikesTable from "../components/EventSpikesTable";
import CompetitorTrendChart from "../components/CompetitorTrendChart";
import MarketTrendChart from "../components/MarketTrendChart";

export default function Dashboard() {
  const [data, setResponse] = useState("");
  const [trigger, setTrigger] = useState(false);

  const handleQuerySubmit = (query) => {
    console.log("User Query:", query);

    axios
      .post("http://127.0.0.1:8000/analyze", { query: query })
      .then((res) => {
        setResponse(res.data.team_b);
        setTrigger(true);
        console.log(res.data.team_b);
      })
      .catch((err) => console.error(err));
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      <SideBar />
      <main className="flex-1 p-6 space-y-6">
        <QueryInput onSubmit={handleQuerySubmit} />

        {trigger ? (
          <div className="grid grid-cols-2 gap-6">
            <ScopeCard summary={data.summary} />
            <MarketInsightsCard insights={data.market_insights} />

            <div>
              <SocialTrendsCard trends={data.social_trends} />
              <CompetitorTrendChart
                timeseries={data.competitor_trend.timeseries}
              />
              <MarketTrendChart
                sectorPerformance={data.market_trend.sector_performance}
              />
              <EventSpikesTable events={data.event_spikes.events_detected} />{" "}
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}
