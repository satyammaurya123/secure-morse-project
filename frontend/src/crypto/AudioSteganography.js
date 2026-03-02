import { argon2id } from 'hash-wasm';

const SALT_BYTES = 32;
const KEY_BYTES = 32; // 256-bit key
const IV_BYTES = 12;

/**
 * Derives a 256-bit key from a password and salt using Argon2id.
 * Settings: 64MB memory, 3 iterations, 1 parallelism.
 * @param {string} password
 * @param {Uint8Array} salt
 * @returns {Promise<Uint8Array>}
 */
export async function deriveKey(password, salt) {
    // Convert password to Uint8Array if it's a string
    const passwordArray = new TextEncoder().encode(password);

    if (salt.length !== SALT_BYTES) {
        throw new Error(`Salt must be ${SALT_BYTES} bytes`);
    }

    // hash-wasm argon2id returns hex by default. We want binary.
    const tempKeyHex = await argon2id({
        password: passwordArray,
        salt: salt,
        parallelism: 1,
        iterations: 3,
        memorySize: 64 * 1024, // 64MB
        hashLength: KEY_BYTES,
        outputType: 'hex', // hash-wasm requires hex or binary. binary depends on version. we'll convert hex to uint8
    });

    // Convert hex string to Uint8Array safely
    const keyMatch = tempKeyHex.match(/.{1,2}/g);
    if (!keyMatch) {
        throw new Error("Failed to derive key: Invalid hex output from Argon2id.");
    }
    return new Uint8Array(keyMatch.map(byte => parseInt(byte, 16)));
}

/**
 * Encrypts data using AES-256-GCM.
 * @param {Uint8Array} data
 * @param {Uint8Array} key 32-byte key
 * @param {Uint8Array} iv 12-byte IV
 * @returns {Promise<Uint8Array>} The encrypted data with appended 16-byte auth tag.
 */
export async function encryptDataGCM(data, key, iv) {
    if (key.length !== KEY_BYTES) throw new Error("Key must be 32 bytes for AES-256-GCM");
    if (iv.length !== IV_BYTES) throw new Error("IV must be 12 bytes");

    const cryptoKey = await window.crypto.subtle.importKey(
        'raw',
        key,
        { name: 'AES-GCM' },
        false,
        ['encrypt']
    );

    const ciphertextBuf = await window.crypto.subtle.encrypt(
        {
            name: 'AES-GCM',
            iv: iv,
            tagLength: 128, // 16 bytes
        },
        cryptoKey,
        data
    );

    return new Uint8Array(ciphertextBuf);
}

/**
 * Decrypts data using AES-256-GCM.
 * @param {Uint8Array} encryptedData Data with appended 16-byte auth tag
 * @param {Uint8Array} key 32-byte key
 * @param {Uint8Array} iv 12-byte IV
 * @returns {Promise<Uint8Array>} The decrypted data.
 */
export async function decryptDataGCM(encryptedData, key, iv) {
    if (key.length !== KEY_BYTES) throw new Error("Key must be 32 bytes for AES-256-GCM");
    if (iv.length !== IV_BYTES) throw new Error("IV must be 12 bytes");

    const cryptoKey = await window.crypto.subtle.importKey(
        'raw',
        key,
        { name: 'AES-GCM' },
        false,
        ['decrypt']
    );

    const plaintextBuf = await window.crypto.subtle.decrypt(
        {
            name: 'AES-GCM',
            iv: iv,
            tagLength: 128, // 16 bytes
        },
        cryptoKey,
        encryptedData
    );

    return new Uint8Array(plaintextBuf);
}

/**
 * ChaCha20 Implementation for PRNG.
 * Generates deterministic pseudo-random sequences based on a Key and Nonce.
 */
export class ChaCha20PRNG {
    /**
     * @param {Uint8Array} key 32-byte seed/key
     * @param {Uint8Array} nonce 12-byte or 8-byte nonce. We will use 12 bytes to match AES.
     */
    constructor(key, nonce) {
        if (key.length !== 32) throw new Error("ChaCha20 needs 32-byte key");

        // Pad or truncate nonce to 12 bytes for 96-bit nonce variant
        const paddedNonce = new Uint8Array(12);
        paddedNonce.set(nonce.slice(0, 12));

        this._state = new Uint32Array(16);
        this._buffer = new Uint8Array(64);
        this._bufferIdx = 64; // Force initial block generation

        // Setup initial state
        const state = this._state;
        const key32 = new Uint32Array(key.buffer, key.byteOffset, 8);
        const nonce32 = new Uint32Array(paddedNonce.buffer, paddedNonce.byteOffset, 3);

        state[0] = 0x61707865;
        state[1] = 0x3320646e;
        state[2] = 0x79622d32;
        state[3] = 0x6b206574;

        for (let i = 0; i < 8; i++) state[4 + i] = key32[i];

        state[12] = 0; // block counter
        state[13] = nonce32[0];
        state[14] = nonce32[1];
        state[15] = nonce32[2];
    }

    _quarterRound(x, a, b, c, d) {
        x[a] = (x[a] + x[b]) >>> 0; x[d] ^= x[a]; x[d] = (x[d] << 16 | x[d] >>> 16) >>> 0;
        x[c] = (x[c] + x[d]) >>> 0; x[b] ^= x[c]; x[b] = (x[b] << 12 | x[b] >>> 20) >>> 0;
        x[a] = (x[a] + x[b]) >>> 0; x[d] ^= x[a]; x[d] = (x[d] << 8 | x[d] >>> 24) >>> 0;
        x[c] = (x[c] + x[d]) >>> 0; x[b] ^= x[c]; x[b] = (x[b] << 7 | x[b] >>> 25) >>> 0;
    }

    _generateBlock() {
        const initialState = this._state;
        const workingState = new Uint32Array(16);
        workingState.set(initialState);

        for (let i = 0; i < 10; i++) {
            this._quarterRound(workingState, 0, 4, 8, 12);
            this._quarterRound(workingState, 1, 5, 9, 13);
            this._quarterRound(workingState, 2, 6, 10, 14);
            this._quarterRound(workingState, 3, 7, 11, 15);
            this._quarterRound(workingState, 0, 5, 10, 15);
            this._quarterRound(workingState, 1, 6, 11, 12);
            this._quarterRound(workingState, 2, 7, 8, 13);
            this._quarterRound(workingState, 3, 4, 9, 14);
        }

        for (let i = 0; i < 16; i++) {
            workingState[i] = (workingState[i] + initialState[i]) >>> 0;
        }

        // Write to buffer
        const dataView = new DataView(this._buffer.buffer);
        for (let i = 0; i < 16; i++) {
            dataView.setUint32(i * 4, workingState[i], true); // little-endian
        }

        // Increment block counter
        this._state[12] = (this._state[12] + 1) >>> 0;
        if (this._state[12] === 0) {
            console.warn("ChaCha20PRNG block counter wrapped! (Exceeded 256GB). Not handled.");
            // In a real crypto implementation, we'd increment state[13], but for PRNG it's fine for our use-case size.
        }

        this._bufferIdx = 0;
    }

    /**
     * Gets next random 32-bit unsigned integer.
     */
    nextUint32() {
        if (this._bufferIdx >= 64) {
            this._generateBlock();
        }
        const dataView = new DataView(this._buffer.buffer, this._bufferIdx, 4);
        const val = dataView.getUint32(0, true);
        this._bufferIdx += 4;
        return val;
    }
}

/**
 * Deterministically shuffles an array in place using Fisher-Yates and ChaCha20 PRNG.
 * @param {Array|TypedArray} array
 * @param {Uint8Array} key 32-byte seed
 * @param {Uint8Array} nonce 12-byte nonce
 */
export function shuffleArrayDeterministic(array, key, nonce) {
    const prng = new ChaCha20PRNG(key, nonce);

    for (let i = array.length - 1; i > 0; i--) {
        // Generate random index between 0 and i inclusive.
        // We use rejection sampling to avoid bias, though simple modulo is often "good enough" for pixels.
        // For security and perfect uniformity, rejection sampling is better.
        let v;
        const max = 0xFFFFFFFF;
        const limit = max - (max % (i + 1));
        do {
            v = prng.nextUint32();
        } while (v >= limit);

        const j = v % (i + 1);

        // Swap
        const temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }
}

// --- PHASE 2: Audio & Embedding Engine ---

const MAGIC_BYTES = new Uint8Array([0x41, 0x56, 0x54, 0x31]); // "AVT1"
const VERSION = 1;

/**
 * Compresses an audio file into an Opus WebM blob using MediaRecorder.
 * @param {File} audioFile
 * @param {Function} onProgress Optional progress callback
 * @returns {Promise<Uint8Array>}
 */
export async function compressAudioToOpus(audioFile, onProgress) {
    return new Promise((resolve, reject) => {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const reader = new FileReader();

        reader.onload = async (e) => {
            try {
                if (onProgress) onProgress("Decoding audio...");
                const audioBuffer = await audioContext.decodeAudioData(e.target.result);

                // Note: OfflineAudioContext does not support createMediaStreamDestination().
                // We must use a standard AudioContext, which means compression happens in real-time (1x speed).
                const source = audioContext.createBufferSource();
                source.buffer = audioBuffer;

                const dest = audioContext.createMediaStreamDestination();
                source.connect(dest);

                const mediaRecorder = new MediaRecorder(dest.stream, {
                    mimeType: 'audio/webm; codecs=opus',
                    audioBitsPerSecond: 64000 // Compress to 64kbps
                });

                const chunks = [];
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) chunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    const arrayBuffer = await blob.arrayBuffer();
                    if (audioContext.state !== 'closed') {
                        audioContext.close();
                    }
                    resolve(new Uint8Array(arrayBuffer));
                };

                if (onProgress) onProgress(`Compressing audio to Opus (takes ~${Math.ceil(audioBuffer.duration)}s in real-time)...`);

                mediaRecorder.start();
                source.start(0);

                // Stop the recorder when the buffer finishes playing
                source.onended = () => {
                    mediaRecorder.stop();
                };

            } catch (err) {
                reject(err);
            }
        };
        reader.onerror = reject;
        reader.readAsArrayBuffer(audioFile);
    });
}

/**
 * Gets ImageData from a File (Image).
 * @param {File} imageFile
 * @returns {Promise<ImageData>}
 */
export async function getImageDataFromFile(imageFile) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const url = URL.createObjectURL(imageFile);
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            URL.revokeObjectURL(url);
            resolve(ctx.getImageData(0, 0, img.width, img.height));
        };
        img.onerror = reject;
        img.src = url;
    });
}

// Bit manipulation helpers
const setLsb = (pixelValue, bit) => (pixelValue & 0xFE) | bit;
const getLsb = (pixelValue) => pixelValue & 1;

/**
 * Embeds bits deterministically into an ImageData.
 * Header is sequential. Payload is scattered via PRNG.
 * @param {ImageData} imageData 
 * @param {Uint8Array} headerData 37 bytes (MAGIC, VAR, SALT)
 * @param {Uint8Array} payloadData (IV, LENGTH, ENCRYPTED_AUDIO_WITH_AUTH)
 * @param {Uint8Array} key 32-byte key derived from Argon2
 */
export function embedPayloadIntoImage(imageData, headerData, payloadData, key) {
    const data = imageData.data;
    const totalPixels = data.length / 4;

    // Header bits: 37 bytes * 8 = 296 bits. We need 99 pixels (using 3 channels per pixel).
    const headerBits = headerData.length * 8;
    const payloadBits = payloadData.length * 8;

    // Capacity check
    const totalBitsNeeded = headerBits + payloadBits;
    const availableBits = totalPixels * 3; // Using RGB, ignoring Alpha

    if (totalBitsNeeded > availableBits) {
        throw new Error(`Capacity exceeded. Need ${totalBitsNeeded} bits, but image only has ${availableBits} bits.`);
    }

    // 1. Embed Header Sequentially
    let bitIndex = 0;
    let pixelOffset = 0;

    for (let i = 0; i < headerData.length; i++) {
        const byte = headerData[i];
        for (let b = 7; b >= 0; b--) {
            const bit = (byte >> b) & 1;

            // Channel: 0=R, 1=G, 2=B
            const channel = bitIndex % 3;
            if (channel === 0 && bitIndex !== 0) pixelOffset += 4; // Move to next pixel

            data[pixelOffset + channel] = setLsb(data[pixelOffset + channel], bit);
            bitIndex++;
        }
    }

    // 2. Prepare PRNG array for the rest of the payload
    // The pixels used by the header are [0 ... Math.floor(headerBits / 3)]
    const headerPixelsUsed = Math.ceil(headerBits / 3);
    const remainingPixelsCount = totalPixels - headerPixelsUsed;

    // Create array of remaining pixel indices
    const pixelIndices = new Uint32Array(remainingPixelsCount);
    for (let i = 0; i < remainingPixelsCount; i++) {
        pixelIndices[i] = headerPixelsUsed + i;
    }

    // We use the SALT as the nonce for ChaCha20 shuffle. Salt is bytes [5...36] in headerData.
    const saltNonce = headerData.slice(5, 5 + 12); // Use first 12 bytes of salt as nonce

    // Shuffle the remaining pixel indices using ChaCha20
    shuffleArrayDeterministic(pixelIndices, key, saltNonce);

    // 3. Embed Payload using pseudo-random pixels
    bitIndex = 0;
    let payloadByteIndex = 0;

    for (let i = 0; i < payloadData.length; i++) {
        const byte = payloadData[i];
        for (let b = 7; b >= 0; b--) {
            const bit = (byte >> b) & 1;

            // To spread bits, we place 3 bits per selected pixel (R, G, B)
            const pixelArrayIndex = Math.floor(bitIndex / 3);
            const channel = bitIndex % 3;

            const pxIndex = pixelIndices[pixelArrayIndex];
            const dataOffset = pxIndex * 4;

            data[dataOffset + channel] = setLsb(data[dataOffset + channel], bit);
            bitIndex++;
        }
    }

    return imageData;
}


/**
 * Extracts payload from an ImageData.
 * @param {ImageData} imageData 
 * @param {Uint8Array} key 32-byte key derived from Argon2
 * @returns {{headerBuf: Uint8Array, payloadBuf: Uint8Array}}
 */
export function extractPayloadFromImage(imageData, key) {
    const data = imageData.data;
    const totalPixels = data.length / 4;

    // 1. Extract Header Sequentially (37 bytes = 296 bits)
    const headerData = new Uint8Array(37);
    let bitIndex = 0;
    let pixelOffset = 0;

    for (let i = 0; i < 37; i++) {
        let byte = 0;
        for (let b = 7; b >= 0; b--) {
            const channel = bitIndex % 3;
            if (channel === 0 && bitIndex !== 0) pixelOffset += 4;

            const bit = getLsb(data[pixelOffset + channel]);
            byte |= (bit << b);
            bitIndex++;
        }
        headerData[i] = byte;
    }

    // Verify MAGIC
    for (let i = 0; i < 4; i++) {
        if (headerData[i] !== MAGIC_BYTES[i]) {
            throw new Error("No Hidden Data: Magic bytes not found.");
        }
    }

    // We don't verify VERSION strict yet, but we will return it.

    const headerBits = 37 * 8;
    const headerPixelsUsed = Math.ceil(headerBits / 3);
    const remainingPixelsCount = totalPixels - headerPixelsUsed;

    // 2. Re-create PRNG mapping
    const pixelIndices = new Uint32Array(remainingPixelsCount);
    for (let i = 0; i < remainingPixelsCount; i++) {
        pixelIndices[i] = headerPixelsUsed + i;
    }

    const saltNonce = headerData.slice(5, 5 + 12);
    shuffleArrayDeterministic(pixelIndices, key, saltNonce);

    // 3. Extract Payload (First need to read IV (12) and LENGTH (4))
    // Payload starts with [IV: 12] [LENGTH: 4]. Total 16 bytes = 128 bits.
    const readBitsFromScattered = (startBitOffset, numBits) => {
        const outBuf = new Uint8Array(Math.ceil(numBits / 8));
        let bitIndex = startBitOffset;
        for (let i = 0; i < outBuf.length; i++) {
            let byte = 0;
            // The last byte might not be fully 8 bits if numBits % 8 !== 0,
            // but in our protocol we always read exact bytes.
            for (let b = 7; b >= 0; b--) {
                const pixelArrayIndex = Math.floor(bitIndex / 3);
                const channel = bitIndex % 3;
                const pxIndex = pixelIndices[pixelArrayIndex];
                const dataOffset = pxIndex * 4;

                const bit = getLsb(data[dataOffset + channel]);
                byte |= (bit << b);
                bitIndex++;
            }
            outBuf[i] = byte;
        }
        return outBuf;
    };

    // Read 16 bytes of metadata (IV + Length)
    const metaBuf = readBitsFromScattered(0, 16 * 8);

    const iv = metaBuf.slice(0, 12);
    const lengthDataView = new DataView(metaBuf.buffer, metaBuf.byteOffset + 12, 4);
    const payloadLength = lengthDataView.getUint32(0, false); // big-endian

    if (payloadLength === 0 || payloadLength > (remainingPixelsCount * 3 / 8)) {
        throw new Error("Corrupt Payload Configuration: Invalid Length Field.");
    }

    // Read the actual encrypted audio (including auth tag)
    // Offset is 16 * 8 bits. We need payloadLength bytes.
    const encryptedAudioBuf = readBitsFromScattered(16 * 8, payloadLength * 8);

    // Pack IV + Length + Encrypted Audio together to match Python logic and return structure
    const fullPayload = new Uint8Array(16 + payloadLength);
    fullPayload.set(metaBuf, 0);
    fullPayload.set(encryptedAudioBuf, 16);

    return {
        headerData,
        payloadData: fullPayload
    };
}

/**
 * Main function to encode an audio file into an image file.
 * @param {File} imageFile 
 * @param {File} audioFile 
 * @param {string} password 
 * @param {Function} onProgress 
 * @returns {Promise<Blob>} The Stego Image as a Blob
 */
export async function encodeAudioIntoImage(imageFile, audioFile, password, onProgress) {
    if (onProgress) onProgress("Starting Audio Compression task...");
    const compressedAudio = await compressAudioToOpus(audioFile, onProgress);

    if (onProgress) onProgress("Deriving encryption keys...");
    const salt = window.crypto.getRandomValues(new Uint8Array(32));
    const key = await deriveKey(password, salt);

    if (onProgress) onProgress("Encrypting audio payload...");
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const encryptedAudioCtx = await encryptDataGCM(compressedAudio, key, iv);

    if (onProgress) onProgress("Preparing image data...");
    const imageData = await getImageDataFromFile(imageFile);

    // Construct Header: MAGIC (4) + VERSION (1) + SALT (32) = 37 bytes
    const headerData = new Uint8Array(37);
    headerData.set(MAGIC_BYTES, 0);
    headerData[4] = VERSION;
    headerData.set(salt, 5);

    // Construct Payload: IV (12) + LENGTH (4) + ENCRYPTED_AUDIO
    const payloadLength = encryptedAudioCtx.length;
    const payloadData = new Uint8Array(16 + payloadLength);
    payloadData.set(iv, 0);

    const lengthDataView = new DataView(payloadData.buffer, payloadData.byteOffset + 12, 4);
    lengthDataView.setUint32(0, payloadLength, false); // big-endian

    payloadData.set(encryptedAudioCtx, 16);

    if (onProgress) onProgress("Embedding payload into image...");
    const stegoImageData = embedPayloadIntoImage(imageData, headerData, payloadData, key);

    if (onProgress) onProgress("Generating final image...");
    return new Promise((resolve) => {
        const canvas = document.createElement('canvas');
        canvas.width = imageData.width;
        canvas.height = imageData.height;
        const ctx = canvas.getContext('2d');
        ctx.putImageData(stegoImageData, 0, 0);

        canvas.toBlob((blob) => {
            resolve(blob);
        }, "image/png"); // always output PNG to preserve LSBs without lossy compression
    });
}

/**
 * Main function to decode an audio file from a stego image file.
 * @param {File} stegoImageFile 
 * @param {string} password 
 * @param {Function} onProgress 
 * @returns {Promise<Blob>} The Decrypted Audio Blob (Opus WebM)
 */
export async function decodeAudioFromImage(stegoImageFile, password, onProgress) {
    if (onProgress) onProgress("Reading image data...");
    const imageData = await getImageDataFromFile(stegoImageFile);

    // Extract first 37 bytes (Header) just to get the salt
    if (onProgress) onProgress("Extracting image header...");
    // We can just call extractPayloadFromImage. It will extract everything. 
    // BUT we need the key first to extract the payload via ChaCha.
    // So we must manually extract the sequential header first to get Salt.

    const data = imageData.data;
    const headerData = new Uint8Array(37);
    let bitIndex = 0;
    let pixelOffset = 0;

    for (let i = 0; i < 37; i++) {
        let byte = 0;
        for (let b = 7; b >= 0; b--) {
            const channel = bitIndex % 3;
            if (channel === 0 && bitIndex !== 0) pixelOffset += 4;
            const bit = getLsb(data[pixelOffset + channel]);
            byte |= (bit << b);
            bitIndex++;
        }
        headerData[i] = byte;
    }

    for (let i = 0; i < 4; i++) {
        if (headerData[i] !== MAGIC_BYTES[i]) {
            throw new Error("No Hidden Data: Magic bytes not found.");
        }
    }

    const salt = headerData.slice(5, 5 + 32);

    if (onProgress) onProgress("Deriving decryption keys from password...");
    const key = await deriveKey(password, salt);

    if (onProgress) onProgress("Extracting scattered payload...");
    const extracted = extractPayloadFromImage(imageData, key);

    const payloadData = extracted.payloadData;
    const iv = payloadData.slice(0, 12);
    const encryptedAudioCtx = payloadData.slice(16);

    if (onProgress) onProgress("Decrypting audio...");
    try {
        const decryptedAudioBytes = await decryptDataGCM(encryptedAudioCtx, key, iv);
        if (onProgress) onProgress("Reconstructing audio file...");
        return new Blob([decryptedAudioBytes], { type: 'audio/webm' });
    } catch (err) {
        throw new Error("Decryption failed. Incorrect password or corrupted payload.");
    }
}
