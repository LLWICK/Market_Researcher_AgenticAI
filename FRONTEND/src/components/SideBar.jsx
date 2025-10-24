import { Home, Search, BarChart2, FileText, Moon, Sun } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import logo from "../assets/logo3.png";

export default function Sidebar() {
  const [dark, setDark] = useState(true);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  };

  return (
    <aside
      className={`w-64 min-h-screen p-4 flex flex-col border-r ${
        dark ? "bg-gray-900 text-white" : "bg-white text-gray-900"
      }`}
    >
      {/* Logo / Title */}
      <div className="flex items-center space-x-2 mb-8">
        <img src={logo} alt="Logo" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-2">
        <Link to={"/dashboard"}>
          <NavItem icon={<Home />} label="Dashboard" />
        </Link>

        <Link to={"/documents"}>
          <NavItem icon={<FileText />} label="Documents" />
        </Link>

        {/* <NavItem icon={<Search />} label="Queries" />
        <NavItem icon={<FileText />} label="Reports" /> */}
      </nav>

      {/* Dark mode toggle */}
      <button
        onClick={() => setDark(!dark)}
        className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700"
      >
        {dark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        <span>{dark ? "Light Mode" : "Dark Mode"}</span>
      </button>

      <div>
        {/* ... other sidebar items ... */}

        <button
          onClick={handleLogout}
          className="p-4 bg-red-600 hover:bg-red-700 rounded m-4"
        >
          Logout
        </button>
      </div>
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
