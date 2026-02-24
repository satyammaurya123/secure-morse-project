import React, { useState } from 'react';
import { UploadCloud, Unlock, CheckCircle, ShieldAlert, Download } from 'lucide-react';
import { motion } from 'framer-motion';
import { decodeImage } from './api';

export default function Decode() {
    const [coverFile, setCoverFile] = useState(null);
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Results
    const [resultType, setResultType] = useState(null); // 'text', 'video', 'audio'
    const [resultText, setResultText] = useState(null);
    const [resultFile, setResultFile] = useState(null); // Base64

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!coverFile || !password) return setError("Cover media and password are required.");

        setLoading(true);
        setError(null);
        setResultType(null);
        setResultText(null);
        setResultFile(null);

        const formData = new FormData();
        formData.append('cover_media', coverFile);
        formData.append('secret_key', password);
        formData.append('method', 'LSB'); // Or make it selectable if needed

        try {
            const res = await decodeImage(formData);
            const { secret_type, message, secret_file } = res.data;

            const type = secret_type || (message ? 'text' : 'unknown');
            setResultType(type);

            if (type === 'text') {
                setResultText(message || res.data.message); // Fallback for old API
            } else {
                setResultFile(secret_file);
            }
        } catch (err) {
            setError(err.response?.data?.error || "Decoding failed. Incorrect password or corrupted media.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card"
            style={{ maxWidth: '600px', margin: '0 auto' }}
        >
            <h2 style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Unlock color="var(--primary)" /> Decode Secure Image
            </h2>

            {error && (
                <div className="alert alert-error">
                    <ShieldAlert size={20} /> {error}
                </div>
            )}

            {resultType ? (
                <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }}>
                    <div className="alert alert-success">
                        <CheckCircle size={20} /> Authentication successful. Secret extracted.
                    </div>
                    {resultType === 'text' ? (
                        <div style={{ marginTop: '1.5rem', padding: '1.5rem', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                            <label className="form-label" style={{ color: 'var(--primary)', marginBottom: '1rem' }}>Decrypted Text</label>
                            <p style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '1.1rem' }}>{resultText}</p>
                        </div>
                    ) : (
                        <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
                            <label className="form-label" style={{ color: 'var(--primary)', marginBottom: '1rem', display: 'block' }}>Decrypted {resultType}</label>
                            {resultType === 'video' ? (
                                <video src={`data:video/mp4;base64,${resultFile}`} controls style={{ width: '100%', borderRadius: '0.5rem' }} />
                            ) : resultType === 'audio' ? (
                                <audio src={`data:audio/mp3;base64,${resultFile}`} controls style={{ width: '100%' }} />
                            ) : null}
                            <div style={{ marginTop: '1rem' }}>
                                <a
                                    href={`data:${resultType === 'video' ? 'video/mp4' : 'audio/mp3'};base64,${resultFile}`}
                                    download={`secret_decrypted.${resultType === 'video' ? 'mp4' : 'mp3'}`}
                                    className="btn btn-primary"
                                    style={{ display: 'inline-flex', padding: '0.5rem 1rem', borderRadius: '0.25rem' }}
                                >
                                    <Download size={18} style={{ marginRight: '0.5rem' }} /> Download Secret {resultType}
                                </a>
                            </div>
                        </div>
                    )}
                    <button
                        onClick={() => setResultType(null)}
                        className="btn btn-secondary"
                        style={{ marginTop: '2rem', width: '100%' }}
                    >
                        Decode Another File
                    </button>
                </motion.div>
            ) : (
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Encoded Media (Cover)</label>
                        <div className="file-input-wrapper" style={{ padding: '2rem' }}>
                            <UploadCloud size={32} color={coverFile ? "var(--primary)" : "var(--text-muted)"} style={{ marginBottom: '0.5rem' }} />
                            <p style={{ color: coverFile ? "var(--text-main)" : "var(--text-muted)", fontWeight: 500 }}>
                                {coverFile ? coverFile.name : "Select the carrier media (Image, Video, Audio)"}
                            </p>
                            <input
                                type="file"
                                accept="image/*, video/*, audio/*"
                                onChange={(e) => setCoverFile(e.target.files[0])}
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Decryption Password</label>
                        <input
                            type="password"
                            className="form-control"
                            placeholder="Enter password used during encoding"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }} disabled={loading}>
                        {loading ? "Decrypting & Extracting..." : "Extract Secret"}
                    </button>
                </form>
            )}
        </motion.div>
    );
}
