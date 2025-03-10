// register.js

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { GoogleOAuthProvider, GoogleLogin } from "@react-oauth/google";
import { PublicClientApplication } from "@azure/msal-browser";

const GOOGLE_CLIENT_ID = ""; // Enter your client id

const MICROSOFT_CLIENT_ID = ""; // Enter your client id

const msalInstance = new PublicClientApplication({
  auth: {
    clientId: MICROSOFT_CLIENT_ID
    // ,redirectUri: "http://localhost:3000",
  },
});

function Register() {
  const [formData, setFormData] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const response = await fetch("http://localhost:8000/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: credentialResponse.credential }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("token", data.access_token);
        navigate("/protected");
      } else {
        setError("Google authentication failed!");
      }
    } catch (error) {
      setError("An error occurred. Please try again.");
    }
  };

  const handleMicrosoftLogin = async () => {
    try {
      await msalInstance.initialize(); // ✅ FIX for uninitialized MSAL error

      const loginResponse = await msalInstance.loginPopup({
        scopes: ["openid", "profile", "email"],
      });

      const idToken = loginResponse.idToken;

      const response = await fetch("http://localhost:8000/auth/microsoft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: idToken }),
      });

      const data = await response.json();
      if (response.ok) {
        localStorage.setItem("token", data.access_token);
        navigate("/protected");
      } else {
        setError("Microsoft authentication failed!");
      }
    } catch (err) {
      console.error("Microsoft login error", err);
      setError("Microsoft login failed.");
    }
  };

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div>
        <h2>Register</h2>
        <form>
          <div>
            <label>Username:</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={(e) =>
                setFormData({ ...formData, username: e.target.value })
              }
              required
            />
          </div>
          <div>
            <label>Password:</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={(e) =>
                setFormData({ ...formData, password: e.target.value })
              }
              required
            />
          </div>
          <button type="submit" disabled={loading}>
            {loading ? "Registering..." : "Register"}
          </button>
        </form>

        {error && <p style={{ color: "red" }}>{error}</p>}

        {/* Google Sign-In Button */}
        <GoogleLogin
          onSuccess={handleGoogleSuccess}
          onError={() => setError("Google login failed")}
        />

        {/* Microsoft Sign-In Button */}
        <button onClick={handleMicrosoftLogin} style={{ marginTop: "1rem" }}>
          Sign in with Microsoft
        </button>
      </div>
    </GoogleOAuthProvider>
  );
}

export default Register;
