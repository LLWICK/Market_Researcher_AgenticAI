import React, { useState } from "react";
import axios from "axios";

const LoginPage = () => {
  const [isSignup, setIsSignup] = useState(true);
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [username, setUsername] = useState("");
  const [message, setMessage] = useState("");

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
      setMessage(res.data.message || "Success!");

      if (!isSignup) {
        localStorage.setItem("token", res.data.access_token);
        localStorage.setItem("username", res.data.username);
      }
    } catch (error) {
      setMessage(error.response?.data?.detail || "Error occurred");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 text-gray-900 flex justify-center items-center">
      <div className="max-w-screen-xl m-0 sm:m-10 bg-white shadow sm:rounded-lg flex justify-center flex-1 overflow-hidden">
        <div className="lg:w-1/2 xl:w-5/12 p-6 sm:p-12">
          <div className="text-center mb-6">
            <img
              src="https://storage.googleapis.com/devitary-image-host.appspot.com/15846435184459982716-LogoMakr_7POjrN.png"
              alt="Logo"
              className="w-32 mx-auto"
            />
          </div>

          <div className="flex flex-col items-center">
            <h1 className="text-2xl xl:text-3xl font-extrabold">
              {isSignup ? "Sign Up" : "Sign In"}
            </h1>

            <form
              onSubmit={handleAuth}
              className="w-full flex-1 mt-8 space-y-5 max-w-sm mx-auto"
            >
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

              {message && (
                <p className="text-center text-sm text-gray-600 mt-2">
                  {message}
                </p>
              )}

              <p className="text-sm text-center text-gray-600 mt-4">
                {isSignup
                  ? "Already have an account?"
                  : "Don’t have an account?"}{" "}
                <button
                  type="button"
                  className="text-indigo-500 hover:underline"
                  onClick={() => {
                    setIsSignup(!isSignup);
                    setMessage("");
                  }}
                >
                  {isSignup ? "Sign In" : "Sign Up"}
                </button>
              </p>
            </form>
          </div>
        </div>

        <div className="flex-1 bg-indigo-100 text-center hidden lg:flex">
          <div
            className="m-12 xl:m-16 w-full bg-contain bg-center bg-no-repeat"
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
