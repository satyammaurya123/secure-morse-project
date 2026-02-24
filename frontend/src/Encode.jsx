import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, Video, Music, Lock, CheckCircle, Download } from 'lucide-react';
import { motion } from 'framer-motion';
import { encodeImage } from './api';

export default function Encode() {
  const [coverFile, setCoverFile] = useState(null);
  const [secretType, setSecretType] = useState('text');
  const [secretText, setSecretText] = useState('');
  const [secretFile, setSecretFile] = useState(null);
  const [password, setPassword] = useState('');
  const [method, setMethod] = useState('LSB');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resultMedia, setResultMedia] = useState(null);
  const [mediaType, setMediaType] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!coverFile || !password) return setError("Cover media and password are required.");
    if (secretType === 'text' && !secretText) return setError("Secret text is required.");
    if (secretType !== 'text' && !secretFile) return setError("Secret file is required.");

    setLoading(true);
    setError(null);
    setResultMedia(null);

    const formData = new FormData();
    formData.append('cover_media', coverFile);
    formData.append('secret_key', password);
    formData.append('method', method);
    formData.append('compress', 'true');
    formData.append('secret_type', secretType);

    if (secretType === 'text') {
      formData.append('secret_text', secretText);
    } else {
      formData.append('secret_file', secretFile);
    }

    try {
      const res = await encodeImage(formData);
      setResultMedia(res.data.encoded_media || res.data.encoded_image);
      setMediaType(res.data.media_type || (coverFile.type || 'image/png'));
    } catch (err) {
      setError(err.response?.data?.error || "An error occurred during encoding.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
      style={{ maxWidth: '800px', margin: '0 auto' }}
    >
      <h2 style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Lock color="var(--primary)" /> Encode Secret Message
      </h2>

      {error && (
        <div className="alert alert-error">
          <CheckCircle size={20} /> {error}
        </div>
      )}

      {resultMedia ? (
        <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} style={{ textAlign: 'center' }}>
          <div className="alert alert-success" style={{ justifyContent: 'center' }}>
            <CheckCircle size={20} /> Encoding Successful!
          </div>
          {mediaType?.startsWith('video/') ? (
            <video
              src={`data:${mediaType};base64,${resultMedia}`}
              controls
              className="preview-image"
              style={{ width: '100%', borderRadius: '0.5rem', marginTop: '1rem' }}
            />
          ) : mediaType?.startsWith('audio/') ? (
            <audio
              src={`data:${mediaType};base64,${resultMedia}`}
              controls
              style={{ width: '100%', marginTop: '1rem' }}
            />
          ) : (
            <img
              src={`data:${mediaType};base64,${resultMedia}`}
              alt="Encoded"
              className="preview-image"
            />
          )}
          <div style={{ marginTop: '2rem' }}>
            <a
              href={`data:${mediaType};base64,${resultMedia}`}
              download={`secure_encoded_media.${mediaType.split('/')[1] || 'bin'}`}
              className="btn btn-primary"
            >
              <Download size={18} /> Download Secure Media
            </a>
            <button
              onClick={() => setResultMedia(null)}
              className="btn btn-secondary"
              style={{ marginLeft: '1rem' }}
            >
              Encode Another
            </button>
          </div>
        </motion.div>
      ) : (
        <form onSubmit={handleSubmit} className="grid-2">
          <div>
            <div className="form-group">
              <label className="form-label">Cover Media</label>
              <div className="file-input-wrapper">
                <UploadCloud size={32} color={coverFile ? "var(--primary)" : "var(--text-muted)"} style={{ marginBottom: '1rem' }} />
                <p style={{ color: coverFile ? "var(--text-main)" : "var(--text-muted)", fontWeight: 500 }}>
                  {coverFile ? coverFile.name : "Upload Image, Video, or Audio"}
                </p>
                <input
                  type="file"
                  accept="image/*, video/*, audio/*"
                  onChange={(e) => setCoverFile(e.target.files[0])}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Steganography Method</label>
              <select
                className="form-control form-select"
                value={method}
                onChange={(e) => setMethod(e.target.value)}
              >
                <option value="LSB">Least Significant Bit (High Capacity)</option>
                <option value="DCT">Discrete Cosine Transform (Robust)</option>
              </select>
            </div>
          </div>

          <div>
            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                Secret Type
              </label>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                <button type="button" className={`btn ${secretType === 'text' ? 'btn-primary' : 'btn-secondary'}`} style={{ flex: 1, padding: '0.5rem' }} onClick={() => setSecretType('text')}>
                  <FileText size={18} /> Text
                </button>
                <button type="button" className={`btn ${secretType === 'video' ? 'btn-primary' : 'btn-secondary'}`} style={{ flex: 1, padding: '0.5rem' }} onClick={() => setSecretType('video')}>
                  <Video size={18} /> Video
                </button>
                <button type="button" className={`btn ${secretType === 'audio' ? 'btn-primary' : 'btn-secondary'}`} style={{ flex: 1, padding: '0.5rem' }} onClick={() => setSecretType('audio')}>
                  <Music size={18} /> Audio
                </button>
              </div>
            </div>

            <div className="form-group">
              {secretType === 'text' ? (
                <>
                  <label className="form-label">Secret Text</label>
                  <textarea
                    className="form-control"
                    rows="4"
                    placeholder="Enter the classified information..."
                    value={secretText}
                    onChange={(e) => setSecretText(e.target.value)}
                  />
                </>
              ) : (
                <>
                  <label className="form-label">Secret File ({secretType})</label>
                  <div className="file-input-wrapper" style={{ padding: '1rem' }}>
                    <UploadCloud size={24} color={secretFile ? "var(--primary)" : "var(--text-muted)"} style={{ marginBottom: '0.5rem' }} />
                    <p style={{ color: secretFile ? "var(--text-main)" : "var(--text-muted)", fontSize: '0.9rem', fontWeight: 500 }}>
                      {secretFile ? secretFile.name : `Upload Secret ${secretType}`}
                    </p>
                    <input
                      type="file"
                      accept={`${secretType}/*`}
                      onChange={(e) => setSecretFile(e.target.files[0])}
                    />
                  </div>
                </>
              )}
            </div>

            <div className="form-group" style={{ marginTop: '1rem' }}>
              <label className="form-label">Encryption Password</label>
              <input
                type="password"
                className="form-control"
                placeholder="Used to derive AES key"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }} disabled={loading}>
              {loading ? "Encrypting & Embedding..." : "Encode to Media"}
            </button>
          </div>
        </form>
      )}
    </motion.div>
  );
}
