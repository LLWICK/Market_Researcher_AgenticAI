import React, { useEffect, useState } from "react";
import SideBar from "../components/SideBar";
import RagDocs2 from "../components/RagDocs2";
import { jwtDecode } from "jwt-decode";

function RagDocumentPage() {
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      const decoded = jwtDecode(token);
      setUserId(decoded.user_id);
    }
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-100">
      <SideBar />
      <div className="flex-1 p-6 grid grid-cols-3 gap-6">
        {/* Main content */}
        <main className="col-span-2 space-y-6">
          <RagDocs2 userId={userId} />
        </main>
      </div>
    </div>
  );
}

export default RagDocumentPage;
