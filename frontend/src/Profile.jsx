import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Trash2, ShieldAlert, X, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import { deleteAccount, logout } from './api';

export default function Profile({ user, setUser }) {
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Google OAuth users (no usable password) are identified by email-as-username
  const isGoogleUser = user?.username?.includes('@');

  const handleOpenModal = () => {
    setShowModal(true);
    setPassword('');
    setConfirmText('');
    setError('');
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setPassword('');
    setConfirmText('');
    setError('');
  };

  const handleDelete = async () => {
    if (confirmText !== 'DELETE') {
      setError('Please type DELETE to confirm.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const payload = isGoogleUser ? {} : { password };
      await deleteAccount(payload);

      // Clear auth state
      await logout().catch(() => {});
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      setUser(null);
      navigate('/');
    } catch (err) {
      const msg =
        err?.response?.data?.error ||
        'Failed to delete account. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const isDeleteReady =
    confirmText === 'DELETE' && (isGoogleUser || password.length > 0);

  return (
    <div className="profile-page animate-fade-in">
      {/* ── Header ── */}
      <div className="profile-header">
        <div className="profile-avatar">
          <User size={40} color="var(--primary)" />
        </div>
        <div>
          <h1 className="profile-username">{user?.username}</h1>
          <p className="profile-subtitle">Account Settings</p>
        </div>
      </div>

      {/* ── Info Card ── */}
      <div className="settings-card">
        <div className="settings-card-header">
          <ShieldAlert size={20} color="var(--primary)" />
          <h2>Account Information</h2>
        </div>
        <div className="info-row">
          <span className="info-label">Username</span>
          <span className="info-value">{user?.username}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Auth Method</span>
          <span className="info-value badge">
            {isGoogleUser ? '🔵 Google OAuth' : '🔐 Email & Password'}
          </span>
        </div>
      </div>

      {/* ── Danger Zone ── */}
      <div className="settings-card danger-zone">
        <div className="settings-card-header">
          <Trash2 size={20} color="#ef4444" />
          <h2 style={{ color: '#ef4444' }}>Danger Zone</h2>
        </div>
        <p className="danger-description">
          Permanently delete your account and all associated data. This action{' '}
          <strong>cannot be undone</strong>.
        </p>
        <button
          id="btn-delete-account"
          className="btn-delete"
          onClick={handleOpenModal}
        >
          <Trash2 size={16} />
          Delete My Account
        </button>
      </div>

      {/* ── Confirmation Modal ── */}
      {showModal && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div
            className="modal-box"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="modal-header">
              <div className="modal-icon-wrap">
                <AlertTriangle size={28} color="#ef4444" />
              </div>
              <button className="modal-close-btn" onClick={handleCloseModal}>
                <X size={20} />
              </button>
            </div>

            <h3 className="modal-title">Delete Account?</h3>
            <p className="modal-body">
              This will permanently remove your account,{' '}
              <strong>all your data</strong>, and cannot be recovered. Are you
              absolutely sure?
            </p>

            {/* Password field — only for non-Google users */}
            {!isGoogleUser && (
              <div className="modal-field">
                <label htmlFor="confirm-password">Current Password</label>
                <div className="password-wrap">
                  <input
                    id="confirm-password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="modal-input"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    className="eye-btn"
                    onClick={() => setShowPassword((v) => !v)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
            )}

            {/* Confirm text */}
            <div className="modal-field">
              <label htmlFor="confirm-text">
                Type <strong>DELETE</strong> to confirm
              </label>
              <input
                id="confirm-text"
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder="DELETE"
                className="modal-input"
                autoComplete="off"
              />
            </div>

            {error && <p className="modal-error">{error}</p>}

            {/* Actions */}
            <div className="modal-actions">
              <button
                className="btn btn-secondary"
                onClick={handleCloseModal}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                id="btn-confirm-delete"
                className="btn-delete"
                onClick={handleDelete}
                disabled={!isDeleteReady || loading}
              >
                {loading ? 'Deleting…' : 'Yes, Delete Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
