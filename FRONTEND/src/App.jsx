import React from "react";
import { Route, Routes } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import MainDashboard from "./pages/MainDashboard";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/dashboard" element={<MainDashboard />} />
    </Routes>
  );
}

export default App;
