import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Key, Shield, ArrowRight, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { forgotPassword, resetPassword } from './api';

export default function ForgotPassword() {
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState('');
    const navigate = useNavigate();

    const handleRequestOtp = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await forgotPassword({ email });
            setSuccessMessage(res.data.message);
            setStep(2);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to request reset code. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleResetPassword = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await resetPassword({ email, otp, new_password: newPassword });
            setSuccessMessage(res.data.message);
            setStep(3);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to reset password. Check your code and try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: '80vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem'
        }}>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="card"
                style={{
                    width: '100%',
                    maxWidth: '480px',
                    background: 'var(--surface)',
                    borderColor: 'rgba(255, 255, 255, 0.05)',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
                    padding: '3rem'
                }}
            >
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <div style={{
                        width: '56px', height: '56px', borderRadius: '1rem',
                        background: 'rgba(99,102,241,0.1)', display: 'inline-flex',
                        alignItems: 'center', justifyContent: 'center',
                        color: 'var(--primary)', marginBottom: '1.5rem',
                        border: '1px solid rgba(99,102,241,0.2)'
                    }}>
                        <Key size={28} />
                    </div>
                    <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                        {step === 1 ? 'Forgot Password' : step === 2 ? 'Reset Password' : 'Password Reset Complete'}
                    </h2>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                        {step === 1 && "Enter your email address and we'll send you a recovery code."}
                        {step === 2 && "Enter the 6-digit code sent to your email and your new password."}
                        {step === 3 && "You can now securely log in with your new password."}
                    </p>
                </div>

                {error && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="alert alert-error"
                        style={{ fontSize: '0.875rem', padding: '0.75rem 1rem', marginBottom: '1.5rem' }}
                    >
                        {error}
                    </motion.div>
                )}
                {successMessage && step !== 3 && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="alert alert-success"
                        style={{ fontSize: '0.875rem', padding: '0.75rem 1rem', marginBottom: '1.5rem', background: 'rgba(34, 197, 94, 0.1)', color: '#4ade80', border: '1px solid rgba(34, 197, 94, 0.2)' }}
                    >
                        {successMessage}
                    </motion.div>
                )}

                {step === 1 && (
                    <form onSubmit={handleRequestOtp} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        <div>
                            <label style={{ fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.5rem', display: 'block', color: 'var(--text-muted)' }}>
                                Email Address
                            </label>
                            <div style={{ position: 'relative' }}>
                                <Mail size={16} style={{
                                    position: 'absolute', top: '50%', left: '1rem',
                                    transform: 'translateY(-50%)', color: 'var(--text-muted)'
                                }} />
                                <input
                                    type="email"
                                    className="form-control"
                                    placeholder="you@example.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    style={{
                                        paddingLeft: '2.75rem', height: '3rem',
                                        background: 'rgba(15,23,42,0.6)',
                                        border: '1px solid rgba(255,255,255,0.08)',
                                        borderRadius: '0.75rem', width: '100%',
                                    }}
                                    required
                                />
                            </div>
                        </div>

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
                                cursor: loading ? 'not-allowed' : 'pointer',
                                opacity: loading ? 0.7 : 1,
                            }}
                        >
                            {loading ? 'Sending Code...' : <><ArrowRight size={18} /> Request Code</>}
                        </button>
                    </form>
                )}

                {step === 2 && (
                    <form onSubmit={handleResetPassword} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        <div>
                            <label style={{ fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.5rem', display: 'block', color: 'var(--text-muted)' }}>
                                Verification Code
                            </label>
                            <div style={{ position: 'relative' }}>
                                <Shield size={16} style={{
                                    position: 'absolute', top: '50%', left: '1rem',
                                    transform: 'translateY(-50%)', color: 'var(--text-muted)'
                                }} />
                                <input
                                    type="text"
                                    className="form-control"
                                    placeholder="123456"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                    maxLength={6}
                                    style={{
                                        paddingLeft: '2.75rem', height: '3rem',
                                        background: 'rgba(15,23,42,0.6)',
                                        border: '1px solid rgba(255,255,255,0.08)',
                                        borderRadius: '0.75rem', width: '100%',
                                        letterSpacing: '0.25rem', fontSize: '1.1rem'
                                    }}
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label style={{ fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.5rem', display: 'block', color: 'var(--text-muted)' }}>
                                New Password
                            </label>
                            <div style={{ position: 'relative' }}>
                                <Key size={16} style={{
                                    position: 'absolute', top: '50%', left: '1rem',
                                    transform: 'translateY(-50%)', color: 'var(--text-muted)'
                                }} />
                                <input
                                    type="password"
                                    className="form-control"
                                    placeholder="••••••••"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    style={{
                                        paddingLeft: '2.75rem', height: '3rem',
                                        background: 'rgba(15,23,42,0.6)',
                                        border: '1px solid rgba(255,255,255,0.08)',
                                        borderRadius: '0.75rem', width: '100%',
                                    }}
                                    required
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading || otp.length < 6 || newPassword.length < 1}
                            style={{
                                height: '3rem', width: '100%',
                                background: 'linear-gradient(to right, var(--primary), var(--secondary))',
                                border: 'none', borderRadius: '0.75rem',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                gap: '0.5rem', fontWeight: 600, marginTop: '0.5rem',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                opacity: loading ? 0.7 : 1,
                            }}
                        >
                            {loading ? 'Resetting...' : 'Reset Password'}
                        </button>
                    </form>
                )}

                {step === 3 && (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{
                            width: '64px', height: '64px', borderRadius: '50%',
                            background: 'rgba(34, 197, 94, 0.1)', display: 'inline-flex',
                            alignItems: 'center', justifyContent: 'center',
                            color: '#4ade80', margin: '1rem 0 2rem'
                        }}>
                            <CheckCircle2 size={32} />
                        </div>
                        <button
                            onClick={() => navigate('/login')}
                            className="btn btn-primary"
                            style={{ width: '100%', height: '3rem' }}
                        >
                            Return to Login
                        </button>
                    </div>
                )}

                {step !== 3 && (
                    <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                        <Link to="/login" style={{ color: 'var(--text-muted)', fontSize: '0.875rem', textDecoration: 'none', fontWeight: 500, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                            <ArrowRight size={14} style={{ transform: 'rotate(180deg)' }} /> Back to login
                        </Link>
                    </div>
                )}
            </motion.div>
        </div>
    );
}
