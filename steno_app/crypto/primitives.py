
import os
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

class AESCipher:
    """Production-ready wrapper for AES-256-GCM encryption."""
    
    @staticmethod
    def generate_key() -> bytes:
        """Generates a cryptographically secure random 32-byte (256-bit) key."""
        return os.urandom(32)

    @staticmethod
    def encrypt(data: bytes, key: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypts data using AES-256-GCM.
        Returns: (ciphertext, nonce, tag)
        """
        if len(key) != 32:
            raise ValueError(f"AES-256 requires exactly a 32-byte key, got {len(key)} bytes.")
            
        nonce = os.urandom(12)  
        
        encryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend()
        ).encryptor()
        
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return ciphertext, nonce, encryptor.tag

    @staticmethod
    def decrypt(ciphertext: bytes, key: bytes, nonce: bytes, tag: bytes) -> bytes:
        """
        Decrypts data using AES-256-GCM and verifies authenticity.
        """
        if len(key) != 32:
            raise ValueError(f"AES-256 requires exactly a 32-byte key, got {len(key)} bytes.")
        if len(nonce) != 12:
            raise ValueError(f"GCM mode requires exactly a 12-byte nonce, got {len(nonce)} bytes.")
            
        decryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        ).decryptor()
        
        return decryptor.update(ciphertext) + decryptor.finalize()

class RSACipher:
    """Wrapper for RSA Key generation and Encryption (OAEP)."""

    @staticmethod
    def generate_keys() -> Tuple[bytes, bytes]:
        """
        Generates RSA-2048 private/public key pair.
        Returns PEM encoded (private_key, public_key).
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return pem_private, pem_public

    @staticmethod
    def encrypt(data: bytes, public_key_pem: bytes) -> bytes:
        """Encrypts data (e.g., session key) with RSA Public Key."""
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )
        
        return public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    @staticmethod
    def decrypt(ciphertext: bytes, private_key_pem: bytes) -> bytes:
        """Decrypts data with RSA Private Key."""
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend()
        )

        return private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

class KeyDerivation:
    """Wrapper for PBKDF2 Key Derivation."""

    @staticmethod
    def derive_key(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Derives a 32-byte key from a password using PBKDF2-HMAC-SHA256.
        Returns (derived_key, salt).
        """
        if salt is None:
            salt = os.urandom(16)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode())
        return key, salt
