
import os
import struct
import zlib
from typing import Tuple, Optional
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.backends import default_backend
from .primitives import AESCipher, RSACipher

class HybridEncryptor:
    """
    Orchestrates the Hybrid Encryption Scheme.
    Format: [ RSA_Enc_Key (256) || IV (12) || Tag (16) || CompressFlag (1) || Ciphertext (var) || HMAC (32) ]
    """

    def __init__(self, recipient_public_key_pem: bytes):
        self.public_key_pem = recipient_public_key_pem

    def encrypt(self, plaintext: bytes, compress: bool = False) -> bytes:
        # 1. Compress if requested
        if compress:
            plaintext = zlib.compress(plaintext)
            comp_flag = b'\x01'
        else:
            comp_flag = b'\x00'

        # 2. Generate ephemeral session key
        session_key = AESCipher.generate_key()

        # 3. Encrypt plaintext with AES-GCM
        ciphertext, iv, tag = AESCipher.encrypt(plaintext, session_key)
        
        # 4. Encrypt session key with RSA
        encrypted_session_key = RSACipher.encrypt(session_key, self.public_key_pem)
        
        # 5. Construct payload body
        # RSA(256) + IV(12) + Tag(16) + Flag(1) + Ciphertext(Var)
        payload_body = encrypted_session_key + iv + tag + comp_flag + ciphertext

        # 6. Compute HMAC-SHA256
        h = hmac.HMAC(session_key, hashes.SHA256(), backend=default_backend())
        h.update(payload_body)
        mac = h.finalize()
        
        return payload_body + mac

class HybridDecryptor:
    """
    Orchestrates Hybrid Decryption.
    """
    
    def __init__(self, private_key_pem: bytes):
        self.private_key_pem = private_key_pem

    def decrypt(self, payload: bytes) -> bytes:
        # Check minimum length
        # RSA(256) + IV(12) + Tag(16) + Flag(1) + HMAC(32) = 317 bytes minimum
        if len(payload) < 317:
            raise ValueError("Payload too short.")

        # Extract components
        encrypted_session_key = payload[:256]
        iv = payload[256:268]
        tag = payload[268:284]
        comp_flag = payload[284:285]
        
        mac = payload[-32:]
        ciphertext = payload[285:-32]
        
        payload_body = payload[:-32]

        # 1. Decrypt Session Key first
        try:
            session_key = RSACipher.decrypt(encrypted_session_key, self.private_key_pem)
        except Exception:
            raise ValueError("Failed to decrypt session key.")

        # 2. Verify HMAC
        h = hmac.HMAC(session_key, hashes.SHA256(), backend=default_backend())
        h.update(payload_body)
        try:
            h.verify(mac)
        except Exception:
            raise ValueError("Integrity Check Failed: HMAC mismatch.")

        # 3. Decrypt Data
        try:
            plaintext = AESCipher.decrypt(ciphertext, session_key, iv, tag)
        except Exception:
            raise ValueError("Decryption Failed: AES-GCM auth tag mismatch.")

        # 4. Decompress if needed
        if comp_flag == b'\x01':
            try:
                plaintext = zlib.decompress(plaintext)
            except zlib.error:
                 raise ValueError("Decompression Failed.")

        return plaintext
