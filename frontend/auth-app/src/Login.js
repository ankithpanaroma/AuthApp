import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

const GOOGLE_CLIENT_ID = "434737298006-vb7bo9vvbehfhoi31qpk7a49neonbe6k.apps.googleusercontent.com";  

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleGoogleSuccess = async (credentialResponse) => {
    console.log('Google Auth Response:', credentialResponse);
    
    try {
      const response = await fetch("http://localhost:8000/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: credentialResponse.credential }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("token", data.access_token);
        navigate('/protected');
      } else {
        setError("Google authentication failed!");
      }
    } catch (error) {
      setError("An error occurred. Please try again.");
    }
  };

  const handleGoogleFailure = () => {
    setError("Google sign-in failed. Try again.");
  };

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div>
        <h2>Login</h2>
        <form>
          <div>
            <label>Username:</label>
            <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div>
            <label>Password:</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <button type="submit" disabled={loading}>{loading ? 'Logging in...' : 'Login'}</button>
        </form>
        {error && <p style={{ color: 'red' }}>{error}</p>}

        {/* Google Sign-In Button */}
        <GoogleLogin onSuccess={handleGoogleSuccess} onError={handleGoogleFailure} />

        <p>Don't have an account? <Link to="/register">Register here</Link></p>
      </div>
    </GoogleOAuthProvider>
  );
}

export default Login;
