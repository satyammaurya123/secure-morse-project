import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, Lock, UserPlus, Mail, Shield, Key, Image, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { signup, verifyEmail } from './api';

export default function Signup({ setUser }) {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [step, setStep] = useState(1);
    const [otp, setOtp] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await signup({ username, email, password });
            setStep(2);
        } catch (err) {
            setError(err.response?.data?.error || 'Authentication failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleVerify = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await verifyEmail({ email, otp });
            localStorage.setItem('access', res.data.access);
            localStorage.setItem('refresh', res.data.refresh);
            setUser({ username: res.data.username });
            navigate('/');
        } catch (err) {
            setError(err.response?.data?.error || 'Verification failed. Please check your code.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="grid-2" style={{
            alignItems: 'center',
            gap: '4rem',
            maxWidth: '1100px',
            margin: '2rem auto',
            padding: '2rem'
        }}>
            {/* Left side info */}
            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5 }}
            >
                <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                    padding: '0.5rem 1rem', background: 'rgba(236, 72, 153, 0.1)',
                    color: 'var(--secondary)', borderRadius: '2rem',
                    fontSize: '0.85rem', fontWeight: 500, marginBottom: '2rem',
                    border: '1px solid rgba(236, 72, 153, 0.2)'
                }}>
                    <Sparkles size={14} />
                    <span>Join the encrypted network</span>
                </div>

                <h1 style={{ fontSize: '3.5rem', lineHeight: 1.1, marginBottom: '1.5rem', fontWeight: 800 }}>
                    Encode. <span style={{ background: 'linear-gradient(to right, var(--primary), var(--secondary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Transmit.</span> Stay private.
                </h1>
                
                <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', marginBottom: '3rem', lineHeight: 1.6 }}>
                    Create your SecureMorse account and start sending end-to-end encoded messages in seconds.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                        <div style={{ background: 'rgba(99, 102, 241, 0.1)', padding: '0.75rem', borderRadius: '0.75rem', color: 'var(--primary)' }}>
                            <Image size={20} />
                        </div>
                        <div>
                            <h4 style={{ fontSize: '1.05rem', marginBottom: '0.25rem' }}>Advanced Steganography</h4>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Hide sensitive text seamlessly inside images or audio files.</p>
                        </div>
                    </div>
                    
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                        <div style={{ background: 'rgba(99, 102, 241, 0.1)', padding: '0.75rem', borderRadius: '0.75rem', color: 'var(--primary)' }}>
                            <Shield size={20} />
                        </div>
                        <div>
                            <h4 style={{ fontSize: '1.05rem', marginBottom: '0.25rem' }}>Military-Grade Encryption</h4>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Secured with AES-256-GCM and RSA-2048 before encoding.</p>
                        </div>
                    </div>
                    
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                        <div style={{ background: 'rgba(99, 102, 241, 0.1)', padding: '0.75rem', borderRadius: '0.75rem', color: 'var(--primary)' }}>
                            <Key size={20} />
                        </div>
                        <div>
                            <h4 style={{ fontSize: '1.05rem', marginBottom: '0.25rem' }}>Zero-Trust Architecture</h4>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Keys are derived locally. We never see your unencrypted data.</p>
                        </div>
                    </div>
                </div>
            </motion.div>

            {/* Right side card */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="card"
                style={{ 
                    background: 'var(--surface)',
                    borderColor: 'rgba(255, 255, 255, 0.05)',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
                    padding: '2.5rem'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                    <div style={{
                        width: '48px', height: '48px', borderRadius: '1rem',
                        background: 'rgba(236, 72, 153, 0.1)', display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                        color: 'var(--secondary)',
                        boxShadow: 'inset 0 0 0 1px rgba(236, 72, 153, 0.2)'
                    }}>
                        <UserPlus size={24} />
                    </div>
                    <div>
                        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem', fontWeight: '700' }}>
                            Create Account
                        </h2>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            Sign up to start encoding
                        </p>
                    </div>
                </div>

                {/* Progress Indicator */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: step >= 1 ? 'var(--text-main)' : 'var(--text-muted)' }}>
                        <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: step >= 1 ? 'var(--secondary)' : 'var(--bg-color)', color: step >= 1 ? 'white' : 'inherit', border: step >= 1 ? 'none' : '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: step >= 1 ? 'bold' : 'normal' }}>1</div>
                        <span>Account</span>
                    </div>
                    <div style={{ height: '1px', flex: 1, background: step >= 2 ? 'var(--secondary)' : 'var(--border-color)', margin: '0 1rem' }}></div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: step >= 2 ? 'var(--text-main)' : 'var(--text-muted)' }}>
                        <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: step >= 2 ? 'var(--secondary)' : 'var(--bg-color)', color: step >= 2 ? 'white' : 'inherit', border: step >= 2 ? 'none' : '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: step >= 2 ? 'bold' : 'normal' }}>2</div>
                        <span>Verify</span>
                    </div>
                    <div style={{ height: '1px', flex: 1, background: 'var(--border-color)', margin: '0 1rem' }}></div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: 'var(--bg-color)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem' }}>3</div>
                        <span>Done</span>
                    </div>
                </div>

                {error && <div className="alert alert-error" style={{ fontSize: '0.9rem', padding: '0.75rem', marginBottom: '1rem' }}>{error}</div>}
                
                {step === 1 ? (
                    <form onSubmit={handleSubmit}>
                    <div className="form-group" style={{ position: 'relative', marginBottom: '1.25rem' }}>
                        <label className="form-label" style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>Username</label>
                        <div style={{ position: 'relative' }}>
                            <User size={18} style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', left: '1rem', color: 'var(--text-muted)' }} />
                            <input
                                type="text"
                                className="form-control"
                                placeholder="Choose a username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                style={{ paddingLeft: '2.75rem', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.05)', height: '2.75rem' }}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group" style={{ position: 'relative', marginBottom: '1.25rem' }}>
                        <label className="form-label" style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>Email</label>
                        <div style={{ position: 'relative' }}>
                            <Mail size={18} style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', left: '1rem', color: 'var(--text-muted)' }} />
                            <input
                                type="email"
                                className="form-control"
                                placeholder="you@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                style={{ paddingLeft: '2.75rem', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.05)', height: '2.75rem' }}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group" style={{ position: 'relative', marginBottom: '2rem' }}>
                        <label className="form-label" style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>Password</label>
                        <div style={{ position: 'relative' }}>
                            <Lock size={18} style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', left: '1rem', color: 'var(--text-muted)' }} />
                            <input
                                type="password"
                                className="form-control"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                style={{ paddingLeft: '2.75rem', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.05)', height: '2.75rem' }}
                                required
                            />
                        </div>
                    </div>

                    <button 
                        type="submit" 
                        className="btn btn-primary" 
                        style={{ 
                            width: '100%', 
                            height: '3rem',
                            background: 'linear-gradient(to right, var(--secondary), var(--primary))',
                            border: 'none',
                            boxShadow: '0 4px 14px 0 rgba(236, 72, 153, 0.39)',
                            marginBottom: '1.5rem'
                        }} 
                        disabled={loading}
                    >
                        {loading ? 'Creating Account...' : <><UserPlus size={18} /> Sign Up</>}
                    </button>
                </form>
                ) : (
                <form onSubmit={handleVerify}>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem', textAlign: 'center' }}>
                        We sent a 6-digit verification code to <strong>{email}</strong>. Please enter it below.
                    </p>
                    <div className="form-group" style={{ position: 'relative', marginBottom: '2rem' }}>
                        <label className="form-label" style={{ fontSize: '0.85rem', marginBottom: '0.5rem', textAlign: 'center', display: 'block' }}>Verification Code</label>
                        <div style={{ position: 'relative' }}>
                            <Shield size={18} style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', left: '1rem', color: 'var(--text-muted)' }} />
                            <input
                                type="text"
                                className="form-control"
                                placeholder="123456"
                                value={otp}
                                onChange={(e) => setOtp(e.target.value)}
                                style={{ paddingLeft: '2.75rem', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.05)', height: '3rem', fontSize: '1.25rem', letterSpacing: '0.25rem', textAlign: 'center' }}
                                maxLength={6}
                                required
                            />
                        </div>
                    </div>

                    <button 
                        type="submit" 
                        className="btn btn-primary" 
                        style={{ 
                            width: '100%', 
                            height: '3rem',
                            background: 'linear-gradient(to right, var(--secondary), var(--primary))',
                            border: 'none',
                            boxShadow: '0 4px 14px 0 rgba(236, 72, 153, 0.39)',
                            marginBottom: '1.5rem'
                        }} 
                        disabled={loading || otp.length < 6}
                    >
                        {loading ? 'Verifying...' : 'Verify Email'}
                    </button>
                </form>
                )}

                <div style={{ textAlign: 'center', borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem' }}>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        Already have an account?{' '}
                        <Link
                            to="/login"
                            style={{
                                color: 'var(--secondary)',
                                fontWeight: 600, textDecoration: 'none', fontSize: '0.9rem'
                            }}
                        >
                            Sign in
                        </Link>
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
