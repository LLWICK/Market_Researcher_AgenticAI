import React from "react";
import { Route, Routes } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import MainDashboard from "./pages/MainDashboard";
import ProtectedRoute from "./routes/ProtectedRoute";
import RagDocumentPage from "./pages/RagDocumentPage";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <MainDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/documents"
        element={
          <ProtectedRoute>
            <RagDocumentPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
