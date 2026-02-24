import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, ArrowRight, UserPlus } from 'lucide-react';
import { motion } from 'framer-motion';
import { login, signup } from './api';

export default function Login({ setUser }) {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            if (isLogin) {
                const res = await login({ username, password });
                localStorage.setItem('access', res.data.access);
                localStorage.setItem('refresh', res.data.refresh);
                setUser({ username: res.data.username });
                navigate('/');
            } else {
                const res = await signup({ username, password });
                localStorage.setItem('access', res.data.access);
                localStorage.setItem('refresh', res.data.refresh);
                setUser({ username: res.data.username });
                navigate('/');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Authentication failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card"
            style={{ maxWidth: '400px', margin: '4rem auto' }}
        >
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div style={{
                    width: '64px', height: '64px', borderRadius: '50%',
                    background: 'rgba(99, 102, 241, 0.1)', display: 'flex',
                    alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem',
                    color: 'var(--primary)'
                }}>
                    <Lock size={32} />
                </div>
                <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>
                    {isLogin ? 'Welcome Back' : 'Create Account'}
                </h2>
                <p style={{ color: 'var(--text-muted)' }}>
                    {isLogin ? 'Enter your credentials to access the secure vault' : 'Sign up to start encoding secure messages'}
                </p>
            </div>

            {error && <div className="alert alert-error" style={{ fontSize: '0.9rem', padding: '0.75rem' }}>{error}</div>}

            <form onSubmit={handleSubmit}>
                <div className="form-group" style={{ position: 'relative' }}>
                    <User size={18} style={{ position: 'absolute', top: '2.4rem', left: '1rem', color: 'var(--text-muted)' }} />
                    <label className="form-label">Username</label>
                    <input
                        type="text"
                        className="form-control"
                        placeholder="Enter username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        style={{ paddingLeft: '2.5rem' }}
                        required
                    />
                </div>

                <div className="form-group" style={{ position: 'relative' }}>
                    <Lock size={18} style={{ position: 'absolute', top: '2.4rem', left: '1rem', color: 'var(--text-muted)' }} />
                    <label className="form-label">Password</label>
                    <input
                        type="password"
                        className="form-control"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        style={{ paddingLeft: '2.5rem' }}
                        required
                    />
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }} disabled={loading}>
                    {loading ? 'Authenticating...' : (isLogin ? <><ArrowRight size={18} /> Sign In</> : <><UserPlus size={18} /> Sign Up</>)}
                </button>
            </form>

            <div style={{ textAlign: 'center', marginTop: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem' }}>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    {isLogin ? "Don't have an account? " : "Already have an account? "}
                    <button
                        type="button"
                        onClick={() => { setIsLogin(!isLogin); setError(null); }}
                        style={{
                            background: 'none', border: 'none', color: 'var(--primary)',
                            fontWeight: 600, cursor: 'pointer', fontSize: '0.9rem'
                        }}
                    >
                        {isLogin ? 'Sign up' : 'Sign in'}
                    </button>
                </p>
            </div>
        </motion.div>
    );
}
