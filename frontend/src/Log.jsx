// src/Log.jsx
import React, { useState, useContext } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { useNavigate, Link } from "react-router-dom";
import { UserContext } from "./UserContext";
import { signInWithGooglePopup } from "./firebase.jsx";
import "./Log.css";

export default function Login() {
  const { setUser } = useContext(UserContext) || {};
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [gloading, setGLoading] = useState(false);
  const navigate = useNavigate();

  const API_BASE = "http://localhost:5001"; // ✅ Correct port (matches Flask backend)

  const formatPhoneForServer = (raw) => {
    if (!raw) return "";
    const s = String(raw).trim();
    if (s.startsWith("+")) return s;
    const digits = s.replace(/\D/g, "");
    if (digits.length === 10) return "+91" + digits;
    return "+" + digits;
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!phone || !password) {
      toast.error("Enter phone and password");
      return;
    }
    const phoneToSend = formatPhoneForServer(phone);
    try {
      setLoading(true);
      const res = await axios.post(
        `${API_BASE}/login`,
        { phone: phoneToSend, password },
        {
          headers: { "Content-Type": "application/json" },
          withCredentials: true,
        }
      );
      if (res.data?.status === "success") {
        const user = res.data.user;
        if (typeof setUser === "function") setUser(user);
        toast.success("Logged in successfully!");
        navigate("/dashboard", { replace: true });
      } else {
        toast.error(res.data?.message || "Login failed");
      }
    } catch (err) {
      console.error("Login error:", err);
      toast.error(err?.response?.data?.message || "Network error");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    try {
      setGLoading(true);
      const idToken = await signInWithGooglePopup();
      const res = await axios.post(
        `${API_BASE}/google-login`,
        { idToken },
        {
          headers: { "Content-Type": "application/json" },
          withCredentials: true,
        }
      );

      if (res.data?.status === "success") {
        const user = res.data.user;
        if (typeof setUser === "function") setUser(user);
        toast.success("Logged in with Google!");
        navigate("/dashboard", { replace: true });
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
              Phone (10 digits)
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="e.g. 9876543210"
                className="field-input"
                inputMode="numeric"
                maxLength={14}
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
