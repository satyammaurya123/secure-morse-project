import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
// import { Lock, Unlock, Shield, Key } from 'lucide-react';
import { Lock, Unlock, Shield } from 'lucide-react';
import { checkAuthStatus, logout } from './api';
import Encode from './Encode';
import Decode from './Decode';
import Login from './Login';
import Signup from './Signup';
import AudioStego from './components/AudioStego';
import './index.css';

function Navbar({ user, setUser }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      setUser(null);
      navigate('/');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <nav className="navbar">
      <Link to="/" className="nav-brand">
        <Shield size={28} color="var(--primary)" />
        SecureMorse
      </Link>
      <div className="nav-links">
        {user ? (
          <>
            <Link to="/encode" className="nav-link">Text Encode</Link>
            <Link to="/decode" className="nav-link">Text Decode</Link>
            <Link to="/audio-stego" className="nav-link">Audio</Link>
            <span className="nav-link" style={{ color: 'var(--primary)' }}>{user.username}</span>
            <button onClick={handleLogout} className="btn btn-secondary" style={{ padding: '0.5rem 1rem' }}>Logout</button>
          </>
        ) : (
          <Link to="/login" className="btn btn-primary">Sign In</Link>
        )}
      </div>
    </nav>
  );
}

function Home() {
  return (
    <div className="hero animate-fade-in">
      <h1>Military-Grade<br />Steganography</h1>
      <p>
        Hide your sensitive communications inside ordinary images using AES-256-GCM, RSA-2048, and Zero-Knowledge principles.
      </p>

      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '2rem', flexWrap: 'wrap' }}>
        <Link to="/encode" className="btn btn-primary">
          <Lock size={18} /> Hide Text
        </Link>
        <Link to="/decode" className="btn btn-secondary">
          <Unlock size={18} /> Extract Text
        </Link>
        <Link to="/audio-stego" className="btn btn-primary" style={{ backgroundColor: 'var(--gray-800)', borderColor: 'var(--gray-700)' }}>
          <Lock size={18} /> Audio Stego
        </Link>
      </div>

      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-value">AES-256</div>
          <div className="stat-label">Military Grade Encryption</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">RSA-2048</div>
          <div className="stat-label">Secure Key Exchange</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">Zero-Trust</div>
          <div className="stat-label">Locally Derived Keys</div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyUser = async () => {
      try {
        const res = await checkAuthStatus();
        if (res.data.authenticated) {
          setUser({ username: res.data.username });
        }
      } catch (err) {
        // Not authenticated
      } finally {
        setLoading(false);
      }
    };
    verifyUser();
  }, []);

  if (loading) return null;

  return (
    <Router>
      <div className="app-container">
        <Navbar user={user} setUser={setUser} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/encode" element={user ? <Encode /> : <Login setUser={setUser} />} />
            <Route path="/decode" element={user ? <Decode /> : <Login setUser={setUser} />} />
            <Route path="/audio-stego" element={user ? <AudioStego /> : <Login setUser={setUser} />} />
            <Route path="/login" element={<Login setUser={setUser} />} />
            <Route path="/signup" element={<Signup setUser={setUser} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
