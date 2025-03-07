import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

const GOOGLE_CLIENT_ID = "434737298006-vb7bo9vvbehfhoi31qpk7a49neonbe6k.apps.googleusercontent.com";  

function Register() {
  const [formData, setFormData] = useState({ username: '', password: '' });
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
        <h2>Register</h2>
        <form>
          <div>
            <label>Username:</label>
            <input type="text" name="username" value={formData.username} onChange={(e) => setFormData({ ...formData, username: e.target.value })} required />
          </div>
          <div>
            <label>Password:</label>
            <input type="password" name="password" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} required />
          </div>
          <button type="submit" disabled={loading}>{loading ? 'Registering...' : 'Register'}</button>
        </form>
        {error && <p style={{ color: 'red' }}>{error}</p>}

        {/* Google Sign-In Button */}
        <GoogleLogin onSuccess={handleGoogleSuccess} onError={handleGoogleFailure} />
      </div>
    </GoogleOAuthProvider>
  );
}

export default Register;
