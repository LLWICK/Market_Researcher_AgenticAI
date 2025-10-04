import SideBar from "../components/SideBar";
import QueryInput from "../components/QueryInput";
import ScopeCard from "../components/ScopeCard";
import TrendChart from "../components/TrendChart";
import axios from "axios";
import { useState } from "react";

export default function Dashboard() {
  const [agentResponse, setResponse] = useState("");

  const handleQuerySubmit = (query) => {
    console.log("User Query:", query);

    axios
      .post("http://127.0.0.1:8000/analyze", { query: query })
      .then((res) => {
        setResponse(res.data.team_b);
        console.log(res.data.team_b);
      })
      .catch((err) => console.error(err));
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      <SideBar />
      <main className="flex-1 p-6 space-y-6">
        <QueryInput onSubmit={handleQuerySubmit} />

        <div className="grid grid-cols-2 gap-6">
          <ScopeCard />
          <TrendChart />
        </div>
      </main>
    </div>
  );
}
