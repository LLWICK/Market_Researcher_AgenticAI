import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import logo from "../assets/logo3.png";
import { ToastContainer, toast, Bounce } from "react-toastify";
import "react-toastify/dist/ReactToastify.css"; // <-- Make sure to import this

const LoginPage = () => {
  const [isSignup, setIsSignup] = useState(true);
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [username, setUsername] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      const endpoint = isSignup ? "register" : "login";
      const payload = isSignup ? { username, ...formData } : formData;

      const res = await axios.post(
        `http://127.0.0.1:8000/${endpoint}`,
        payload
      );

      // ✅ Show success toast
      toast.success(res.data.message || "Success!", {
        position: "top-center",
        autoClose: 3000,
        transition: Bounce,
      });

      if (!isSignup) {
        localStorage.setItem("token", res.data.access_token);
        localStorage.setItem("username", res.data.username);

        // Small delay before navigation so toast shows briefly
        setTimeout(() => navigate("/dashboard"), 1000);
      } else {
        // Clear form after successful signup
        setFormData({ email: "", password: "" });
        setUsername("");
        setIsSignup(false);
      }
    } catch (error) {
      const errMsg = error.response?.data?.detail || "An error occurred!";
      toast.error(errMsg, {
        position: "top-center",
        autoClose: 4000,
        transition: Bounce,
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 text-gray-900">
      <ToastContainer theme="light" />
      <div className="w-full max-w-6xl bg-white shadow-lg rounded-lg flex flex-col lg:flex-row overflow-hidden h-[90vh]">
        {/* --- Left Section (Form) --- */}
        <div className="w-full lg:w-1/2 flex flex-col justify-center items-center p-8 sm:p-12">
          <div className="text-center mb-6">
            <img src={logo} alt="Logo" className="w-100" />
          </div>

          <h1 className="text-2xl xl:text-3xl font-extrabold mb-6">
            {isSignup ? "Sign Up" : "Sign In"}
          </h1>

          <form onSubmit={handleAuth} className="w-full max-w-sm space-y-5">
            {isSignup && (
              <input
                type="text"
                name="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                required
                className="w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-indigo-400 focus:bg-white"
              />
            )}

            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Email"
              required
              className="w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-indigo-400 focus:bg-white"
            />

            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Password"
              required
              className="w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-indigo-400 focus:bg-white"
            />

            <button
              type="submit"
              className="mt-5 tracking-wide font-semibold bg-indigo-500 text-gray-100 w-full py-4 rounded-lg hover:bg-indigo-700 transition-all duration-300 ease-in-out flex items-center justify-center focus:shadow-outline focus:outline-none"
            >
              <svg
                className="w-6 h-6 -ml-2"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                <circle cx="8.5" cy="7" r="4" />
                {isSignup && <path d="M20 8v6M23 11h-6" />}
              </svg>
              <span className="ml-3">{isSignup ? "Sign Up" : "Sign In"}</span>
            </button>

            <p className="text-sm text-center text-gray-600 mt-4">
              {isSignup ? "Already have an account?" : "Don’t have an account?"}{" "}
              <button
                type="button"
                className="text-indigo-500 hover:underline"
                onClick={() => setIsSignup(!isSignup)}
              >
                {isSignup ? "Sign In" : "Sign Up"}
              </button>
            </p>
          </form>
        </div>

        {/* --- Right Section (Illustration) --- */}
        <div className="hidden lg:flex w-1/2 bg-indigo-100 items-center justify-center">
          <div
            className="w-4/5 h-4/5 bg-contain bg-center bg-no-repeat"
            style={{
              backgroundImage:
                "url('https://storage.googleapis.com/devitary-image-host.appspot.com/15848031292911696601-undraw_designer_life_w96d.svg')",
            }}
          ></div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
