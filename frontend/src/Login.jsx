import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, Lock, ArrowRight, Shield, Cpu, Eye, EyeOff } from 'lucide-react';
import { motion } from 'framer-motion';
import { login, googleLogin } from './api';
import { GoogleLogin } from '@react-oauth/google';

export default function Login({ setUser }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showPassword, setShowPassword] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await login({ username, password });
            localStorage.setItem('access', res.data.access);
            localStorage.setItem('refresh', res.data.refresh);
            setUser({ username: res.data.username });
            navigate('/');
        } catch (err) {
            setError(err.response?.data?.error || 'Authentication failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };
    const handleGoogleSuccess = async (credentialResponse) => {
        setLoading(true);
        setError(null);
        try {
            const res = await googleLogin({ token: credentialResponse.credential });
            localStorage.setItem('access', res.data.access);
            localStorage.setItem('refresh', res.data.refresh);
            setUser({ username: res.data.username });
            navigate('/');
        } catch (err) {
            setError(err.response?.data?.error || 'Google authentication failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            background: 'var(--background)',
        }}>
            {/* LEFT SIDE — Branding */}
            <motion.div
                initial={{ opacity: 0, x: -40 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    padding: '4rem',
                    background: 'linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(236,72,153,0.05) 100%)',
                    borderRight: '1px solid rgba(255,255,255,0.05)',
                    display: window.innerWidth < 768 ? 'none' : 'flex',
                }}
            >
                <div style={{ maxWidth: '480px' }}>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <span style={{
                            display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                            background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)',
                            borderRadius: '999px', padding: '0.4rem 1rem',
                            fontSize: '0.8rem', color: 'var(--primary)', marginBottom: '2rem'
                        }}>
                             Secure Authentication
                        </span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        style={{ fontSize: '3rem', fontWeight: 800, lineHeight: 1.1, marginBottom: '1.5rem' }}
                    >
                        Welcome<br />
                        <span style={{ background: 'linear-gradient(to right, var(--primary), var(--secondary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                            Back.
                        </span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        style={{ color: 'var(--text-muted)', fontSize: '1.1rem', lineHeight: 1.7, marginBottom: '3rem' }}
                    >
                        Your encrypted messages are waiting. Sign in to access your secure vault.
                    </motion.p>

                    {/* Feature list */}
                    {[
                        { icon: Shield, title: 'End-to-End Encrypted', desc: 'Messages secured with AES-256-GCM' },
                        { icon: Cpu, title: 'Steganography Engine', desc: 'Hide data inside images & audio' },
                    ].map(({ icon: Icon, title, desc }, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.5 + i * 0.1 }}
                            style={{
                                display: 'flex', alignItems: 'flex-start', gap: '1rem',
                                marginBottom: '1.5rem'
                            }}
                        >
                            <div style={{
                                width: '40px', height: '40px', borderRadius: '0.75rem',
                                background: 'rgba(99,102,241,0.1)', display: 'flex',
                                alignItems: 'center', justifyContent: 'center',
                                color: 'var(--primary)', flexShrink: 0,
                                border: '1px solid rgba(99,102,241,0.2)'
                            }}>
                                <Icon size={18} />
                            </div>
                            <div>
                                <p style={{ fontWeight: 600, marginBottom: '0.2rem', fontSize: '0.95rem' }}>{title}</p>
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{desc}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </motion.div>

            {/* RIGHT SIDE — Form */}
            <motion.div
                initial={{ opacity: 0, x: 40 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                style={{
                    width: '480px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    padding: '3rem',
                    flexShrink: 0,
                }}
            >
                {/* Header */}
                <div style={{ marginBottom: '2.5rem' }}>
                    <div style={{
                        width: '48px', height: '48px', borderRadius: '0.875rem',
                        background: 'rgba(99,102,241,0.1)', display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                        color: 'var(--primary)', marginBottom: '1.5rem',
                        border: '1px solid rgba(99,102,241,0.2)'
                    }}>
                        <Lock size={22} />
                    </div>
                    <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Sign In</h2>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        Enter your credentials to continue
                    </p>
                </div>

                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="alert alert-error"
                        style={{ fontSize: '0.875rem', padding: '0.75rem 1rem', marginBottom: '1.5rem' }}
                    >
                        {error}
                    </motion.div>
                )}

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {/* Username */}
                    <div>
                        <label style={{ fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.5rem', display: 'block', color: 'var(--text-muted)' }}>
                            Username
                        </label>
                        <div style={{ position: 'relative' }}>
                            <User size={16} style={{
                                position: 'absolute', top: '50%', left: '1rem',
                                transform: 'translateY(-50%)', color: 'var(--text-muted)'
                            }} />
                            <input
                                type="text"
                                className="form-control"
                                placeholder="Enter your username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                style={{
                                    paddingLeft: '2.75rem', height: '3rem',
                                    background: 'rgba(15,23,42,0.6)',
                                    border: '1px solid rgba(255,255,255,0.08)',
                                    borderRadius: '0.75rem', width: '100%',
                                    transition: 'border-color 0.2s'
                                }}
                                required
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div>
                        <label style={{ fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.5rem', display: 'block', color: 'var(--text-muted)' }}>
                            Password
                        </label>
                        <div style={{ position: 'relative' }}>
                            <Lock size={16} style={{
                                position: 'absolute', top: '50%', left: '1rem',
                                transform: 'translateY(-50%)', color: 'var(--text-muted)'
                            }} />
                            <input
                                type={showPassword ? 'text' : 'password'}
                                className="form-control"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                style={{
                                    paddingLeft: '2.75rem', paddingRight: '3rem',
                                    height: '3rem',
                                    background: 'rgba(15,23,42,0.6)',
                                    border: '1px solid rgba(255,255,255,0.08)',
                                    borderRadius: '0.75rem', width: '100%',
                                }}
                                required
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                style={{
                                    position: 'absolute', top: '50%', right: '1rem',
                                    transform: 'translateY(-50%)', background: 'none',
                                    border: 'none', color: 'var(--text-muted)', cursor: 'pointer',
                                    padding: 0
                                }}
                            >
                                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                            </button>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                            <Link to="/forgot-password" style={{ fontSize: '0.85rem', color: 'var(--primary)', textDecoration: 'none', fontWeight: 500 }}>
                                Forgot Password?
                            </Link>
                        </div>
                    </div>

                    {/* Submit */}
                    <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={loading}
                        style={{
                            height: '3rem', width: '100%',
                            background: 'linear-gradient(to right, var(--primary), var(--secondary))',
                            border: 'none', borderRadius: '0.75rem',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            gap: '0.5rem', fontWeight: 600, marginTop: '0.5rem',
                            boxShadow: '0 4px 14px rgba(99,102,241,0.35)',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            opacity: loading ? 0.7 : 1,
                        }}
                    >
                        {loading ? 'Signing in...' : <><ArrowRight size={18} /> Sign In</>}
                    </button>
                    
                    <div style={{ display: 'flex', alignItems: 'center', margin: '0.5rem 0' }}>
                        <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.1)' }} />
                        <span style={{ margin: '0 1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>OR</span>
                        <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.1)' }} />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                        <GoogleLogin
                            onSuccess={handleGoogleSuccess}
                            onError={() => setError('Google sign in failed.')}
                            theme="filled_black"
                            shape="rectangular"
                        />
                    </div>
                </form>

                {/* Footer */}
                <p style={{ textAlign: 'center', marginTop: '2rem', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    Don't have an account?{' '}
                    <Link to="/signup" style={{ color: 'var(--primary)', fontWeight: 600, textDecoration: 'none' }}>
                        Sign up
                    </Link>
                </p>
            </motion.div>
        </div>
    );
}