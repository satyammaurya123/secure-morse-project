import React, { useState, useRef } from 'react';
import { Upload, FileAudio, FileImage, ShieldCheck, Download, AlertCircle, PlayCircle, Lock, Unlock, Database } from 'lucide-react';
import { encodeAudioIntoImage, decodeAudioFromImage } from '../crypto/AudioSteganography';
import { registerAudioStego, verifyAudioStego } from '../api';

export default function AudioStego() {
    const [mode, setMode] = useState('encode'); // 'encode' or 'decode'

    // Encode State
    const [encImage, setEncImage] = useState(null);
    const [encAudio, setEncAudio] = useState(null);
    const [encPassword, setEncPassword] = useState('');
    const [encProgress, setEncProgress] = useState('');
    const [encResultUrl, setEncResultUrl] = useState(null);
    const [encError, setEncError] = useState('');
    const [encLoading, setEncLoading] = useState(false);

    // Decode State
    const [decImage, setDecImage] = useState(null);
    const [decPassword, setDecPassword] = useState('');
    const [decProgress, setDecProgress] = useState('');
    const [decResultUrl, setDecResultUrl] = useState(null);
    const [decError, setDecError] = useState('');
    const [decLoading, setDecLoading] = useState(false);
    const [verified, setVerified] = useState(false); // Indicates backend has authorized extraction

    // --- Handlers for Encode ---
    const handleEncodeSubmit = async (e) => {
        e.preventDefault();
        if (!encImage || !encAudio || !encPassword) {
            setEncError('Please provide an image, an audio file, and a password.');
            return;
        }

        setEncError('');
        setEncLoading(true);
        setEncResultUrl(null);

        try {
            // 1. Client-side Processing
            const stegoBlob = await encodeAudioIntoImage(encImage, encAudio, encPassword, setEncProgress);

            // Calculate Hash for Backend Tracking
            setEncProgress("Registering image with backend...");
            const buf = await stegoBlob.arrayBuffer();
            const hashBuffer = await window.crypto.subtle.digest('SHA-256', buf);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

            // 2. Register with Backend
            await registerAudioStego({
                image_hash: hashHex,
                version: 1
            });

            const url = URL.createObjectURL(stegoBlob);
            setEncResultUrl(url);
            setEncProgress('Encoding and Registration Complete!');

        } catch (err) {
            console.error(err);
            setEncError(err.message || 'An error occurred during encoding.');
            setEncProgress('');
        } finally {
            setEncLoading(false);
        }
    };

    // --- Handlers for Decode ---
    const handleVerify = async (e) => {
        e.preventDefault();
        if (!decImage) {
            setDecError('Please provide a steganography image.');
            return;
        }

        setDecError('');
        setDecLoading(true);
        setDecProgress('Verifying image integrity and authorization with backend...');

        try {
            // 1. Send image to Backend for Verification & Authorization (Gatekeeper)
            const formData = new FormData();
            formData.append('image', decImage);

            const res = await verifyAudioStego(formData);

            if (res.data.status === 'verified') {
                setVerified(true);
                setDecProgress('Backend Verification Passed. Ready for client-side extraction.');
            } else {
                throw new Error("Verification failed unexpectedly.");
            }
        } catch (err) {
            console.error(err);
            if (err.response?.data?.error) {
                setDecError(`Backend Error: ${err.response.data.error}`);
            } else {
                setDecError(err.message || 'An error occurred during backend verification.');
            }
            setDecProgress('');
        } finally {
            setDecLoading(false);
        }
    };

    const handleDecodeSubmit = async (e) => {
        e.preventDefault();
        if (!verified) {
            setDecError('You must verify the image with the backend first.');
            return;
        }
        if (!decPassword) {
            setDecError('Please enter the password to decrypt the payload.');
            return;
        }

        setDecError('');
        setDecLoading(true);
        setDecResultUrl(null);

        try {
            // 2. Client-side full extraction & decryption
            const audioBlob = await decodeAudioFromImage(decImage, decPassword, setDecProgress);
            const url = URL.createObjectURL(audioBlob);
            setDecResultUrl(url);
            setDecProgress('Audio Extracted Successfully!');
        } catch (err) {
            console.error(err);
            setDecError(`Extraction Failed: ${err.message}`);
            setDecProgress('');
        } finally {
            setDecLoading(false);
        }
    };

    return (
        <div className="animate-fade-in" style={{ maxWidth: '800px', margin: '0 auto' }}>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
                <FileAudio size={28} color="var(--primary)" />
                Audio Steganography
            </h2>

            <p style={{ color: 'var(--gray-300)', marginBottom: '2rem' }}>
                Securely embed audio files inside images using AES-256-GCM and client-side processing. Audio payloads are compressed automatically to Opus format to minimize size. Verification is handled by the backend gatekeeper.
            </p>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
                <button
                    className={`btn ${mode === 'encode' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setMode('encode')}
                >
                    <Lock size={18} /> Hide Audio
                </button>
                <button
                    className={`btn ${mode === 'decode' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => {
                        setMode('decode');
                        setVerified(false); // reset verification state
                        setDecProgress('');
                        setDecResultUrl(null);
                        setDecError('');
                    }}
                >
                    <Unlock size={18} /> Extract Audio
                </button>
            </div>

            {mode === 'encode' ? (
                <div className="card">
                    <form onSubmit={handleEncodeSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        <div>
                            <label>Cover Image (PNG/JPG)</label>
                            <input
                                type="file"
                                accept="image/png, image/jpeg"
                                className="input-field"
                                onChange={(e) => setEncImage(e.target.files[0])}
                                disabled={encLoading}
                            />
                        </div>

                        <div>
                            <label>Secret Audio (WAV/MP3)</label>
                            <input
                                type="file"
                                accept="audio/*"
                                className="input-field"
                                onChange={(e) => setEncAudio(e.target.files[0])}
                                disabled={encLoading}
                            />
                            <small style={{ color: 'var(--gray-400)' }}>Audio will be automatically compressed client-side before embedding.</small>
                        </div>

                        <div>
                            <label>Encryption Password</label>
                            <input
                                type="password"
                                className="input-field"
                                value={encPassword}
                                onChange={(e) => setEncPassword(e.target.value)}
                                placeholder="Enter a strong password"
                                disabled={encLoading}
                            />
                        </div>

                        <button type="submit" className="btn btn-primary" disabled={encLoading || !encImage || !encAudio || !encPassword}>
                            {encLoading ? 'Processing...' : 'Encrypt & Embed'}
                        </button>

                        {encProgress && (
                            <div style={{ padding: '1rem', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '0.9rem' }}>
                                <span className="animate-pulse">⚡</span> {encProgress}
                            </div>
                        )}

                        {encError && (
                            <div style={{ color: 'var(--error)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <AlertCircle size={18} /> {encError}
                            </div>
                        )}

                        {encResultUrl && (
                            <div style={{ marginTop: '1rem', padding: '1.5rem', border: '1px solid var(--primary)', borderRadius: '8px', textAlign: 'center' }}>
                                <ShieldCheck size={48} color="var(--primary)" style={{ margin: '0 auto 1rem auto' }} />
                                <h3 style={{ marginBottom: '1rem' }}>Steganography Complete!</h3>
                                <a href={encResultUrl} download={`stego_audio_${Date.now()}.png`} className="btn btn-primary">
                                    <Download size={18} /> Download Stego Image
                                </a>
                                <p style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--gray-400)' }}>
                                    This image now securely contains your audio payload.
                                </p>
                            </div>
                        )}
                    </form>
                </div>
            ) : (
                <div className="card">
                    {/* Phase 1: Verify */}
                    {!verified ? (
                        <form onSubmit={handleVerify} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                            <div>
                                <label>Stego Image (PNG)</label>
                                <input
                                    type="file"
                                    accept="image/png"
                                    className="input-field"
                                    onChange={(e) => setDecImage(e.target.files[0])}
                                    disabled={decLoading}
                                />
                                <small style={{ color: 'var(--gray-400)' }}>The image must be sent to the backend to verify Magic bytes and extraction authorization.</small>
                            </div>

                            <button type="submit" className="btn btn-secondary" disabled={decLoading || !decImage}>
                                {decLoading ? 'Verifying...' : <><Database size={18} /> Verify via Backend Gatekeeper</>}
                            </button>
                        </form>
                    ) : (
                        /* Phase 2: Decrypt */
                        <form onSubmit={handleDecodeSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                            <div style={{ padding: '1rem', backgroundColor: 'rgba(56, 189, 248, 0.1)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <ShieldCheck size={20} />
                                Image Verified! You requested extraction authorization from the server and it was granted.
                            </div>

                            <div>
                                <label>Decryption Password</label>
                                <input
                                    type="password"
                                    className="input-field"
                                    value={decPassword}
                                    onChange={(e) => setDecPassword(e.target.value)}
                                    placeholder="Enter the password used during embedding"
                                    disabled={decLoading}
                                />
                                <small style={{ color: 'var(--gray-400)' }}>Decryption and decompression happen 100% locally in your browser.</small>
                            </div>

                            <button type="submit" className="btn btn-primary" disabled={decLoading || !decPassword}>
                                {decLoading ? 'Extracting...' : 'Extract Hidden Audio'}
                            </button>
                        </form>
                    )}

                    {decProgress && (
                        <div style={{ padding: '1rem', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '0.9rem', marginTop: '1rem' }}>
                            <span className="animate-pulse">⚡</span> {decProgress}
                        </div>
                    )}

                    {decError && (
                        <div style={{ color: 'var(--error)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                            <AlertCircle size={18} /> {decError}
                        </div>
                    )}

                    {decResultUrl && (
                        <div style={{ marginTop: '1.5rem', padding: '1.5rem', border: '1px solid var(--primary)', borderRadius: '8px', textAlign: 'center' }}>
                            <PlayCircle size={48} color="var(--primary)" style={{ margin: '0 auto 1rem auto' }} />
                            <h3 style={{ marginBottom: '1rem' }}>Audio Decoded!</h3>
                            <audio controls src={decResultUrl} style={{ width: '100%', marginBottom: '1rem', outline: 'none' }} />
                            <a href={decResultUrl} download="secret_audio.webm" className="btn btn-secondary" style={{ width: '100%' }}>
                                <Download size={18} /> Download Decoded Audio
                            </a>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
