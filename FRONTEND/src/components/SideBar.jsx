import { Home, Search, BarChart2, FileText, Moon, Sun } from "lucide-react";
import { useState } from "react";

export default function Sidebar() {
  const [dark, setDark] = useState(false);

  return (
    <aside
      className={`w-64 min-h-screen p-4 flex flex-col border-r ${
        dark ? "bg-gray-900 text-white" : "bg-white text-gray-900"
      }`}
    >
      {/* Logo / Title */}
      <div className="flex items-center space-x-2 mb-8">
        <BarChart2 className="w-6 h-6 text-blue-500" />
        <h1 className="text-xl font-bold">Agentic AI</h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-2">
        <NavItem icon={<Home />} label="Dashboard" />
        <NavItem icon={<Search />} label="Queries" />
        <NavItem icon={<FileText />} label="Reports" />
      </nav>

      {/* Dark mode toggle */}
      <button
        onClick={() => setDark(!dark)}
        className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700"
      >
        {dark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        <span>{dark ? "Light Mode" : "Dark Mode"}</span>
      </button>
    </aside>
  );
}

function NavItem({ icon, label }) {
  return (
    <button className="flex items-center w-full space-x-2 p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700">
      {icon}
      <span>{label}</span>
    </button>
  );
}
