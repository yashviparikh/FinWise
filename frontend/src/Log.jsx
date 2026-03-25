// src/Log.jsx (email/username login)
import React, { useState, useContext } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { UserContext } from "./UserContext";
import { signInWithGooglePopup } from "./firebase.jsx";
import "./Log.css";

const API_BASE = "http://127.0.0.1:5000";

export default function Login() {
  const { setUser } = useContext(UserContext) || {};
  const [identifier, setIdentifier] = useState(""); // email or username
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [gloading, setGLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const submit = async (e) => {
    e.preventDefault();
    if (!identifier || !password) {
      toast.error("Enter email/username and password");
      return;
    }
    try {
      setLoading(true);
      const payload = identifier.includes("@")
        ? { email: identifier, password }
        : { username: identifier, password };
      const res = await axios.post(`${API_BASE}/auth/login`, payload, {
        headers: { "Content-Type": "application/json" },
        withCredentials: true,
      });
      if (res.data?.status === "success" && res.data?.user) {
        const user = res.data.user;
        if (typeof setUser === "function") setUser(user);
  toast.success("Logged in successfully!");
  const dest = location.state?.from?.pathname || "/dashboard";
  navigate(dest, { replace: true });
      } else {
        toast.error(res.data?.message || "Login failed");
      }
    } catch (err) {
      console.error("Login error:", err);
      toast.error(err?.response?.data?.message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    try {
      setGLoading(true);
      const idToken = await signInWithGooglePopup();
      const res = await axios.post(
        `${API_BASE}/auth/google-login`,
        { idToken },
        {
          headers: { "Content-Type": "application/json" },
          withCredentials: true,
        }
      );

      if (res.data?.status === "success" && res.data?.user) {
        const user = res.data.user;
        if (typeof setUser === "function") setUser(user);
  toast.success("Logged in with Google!");
  const dest = location.state?.from?.pathname || "/dashboard";
  navigate(dest, { replace: true });
      } else {
        toast.error(res.data?.message || "Google login failed");
      }
    } catch (err) {
      console.error("Google login error:", err);
      toast.error(err?.message || "Google sign-in failed");
    } finally {
      setGLoading(false);
    }
  };

  return (
    <div className="login-page">
      <main className="login-main">
        <div className="login-card" role="form" aria-label="Login form">
          <h2 className="login-title">Welcome back</h2>

          <form onSubmit={submit} className="login-form">
            <label className="field-label">
              Email or Username
              <input
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="your@email.com or username"
                className="field-input"
                autoComplete="username"
              />
            </label>

            <label className="field-label">
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your password"
                className="field-input"
                autoComplete="current-password"
              />
            </label>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </button>

            <div style={{ height: 12 }} />

            <button
              type="button"
              className="btn-google"
              onClick={handleGoogleSignIn}
              disabled={gloading}
            >
              {gloading ? "Opening..." : "Continue with Google"}
            </button>
          </form>

          <div className="login-footer">
            <div>
              New here? <Link to="/signup" className="link">Create an account</Link>
            </div>
            <div>
              <Link to="/forgot-password" className="link">Forgot password?</Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
