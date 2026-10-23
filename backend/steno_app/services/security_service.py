
import binascii
from typing import Tuple
from ..crypto.primitives import RSACipher, KeyDerivation 
from ..crypto.hybrid import HybridEncryptor, HybridDecryptor

class SecurityService:
    """
    High-level service for handling:
    - User key management (RSA key generation/loading)
    - Hybrid Encryption/Decryption flow
    - Format conversion (Hex/Base64)
    """
    
    @staticmethod
    def generate_user_keys() -> Tuple[str, str]:
        """
        Generates a new RSA-2048 key pair for a user.
        Returns PEM strings as (private_key, public_key).
        """
        priv, pub = RSACipher.generate_keys()
        return priv.decode('utf-8'), pub.decode('utf-8')

    @staticmethod
    def encrypt_payload(plaintext: str, recipient_public_key_pem: str, compress: bool = False) -> str:
        """
        Encrypts plaintext using Hybrid Scheme.
        Returns Hex string of the encrypted binary payload.
        """
        encryptor = HybridEncryptor(recipient_public_key_pem.encode('utf-8'))
        encrypted_bytes = encryptor.encrypt(plaintext.encode('utf-8'), compress=compress)
        return binascii.hexlify(encrypted_bytes).decode('utf-8')

    @staticmethod
    def decrypt_payload(ciphertext_hex: str, private_key_pem: str) -> str:
        """
        Decrypts Hex string using Hybrid Scheme.
        Returns decrypted plaintext string.
        """
        try:
            encrypted_bytes = binascii.unhexlify(ciphertext_hex)
            decryptor = HybridDecryptor(private_key_pem.encode('utf-8'))
            decrypted_bytes = decryptor.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8') # Assuming UTF-8 text
        except Exception as e:
            # Re-raise with clean error message
            raise ValueError(f"Decryption failed: {str(e)}")

    @staticmethod
    def derive_encryption_key(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Derives an encryption key from a password.
        Useful if we want to encrypt the Private Key at rest (future enhancement).
        """
        return KeyDerivation.derive_key(password, salt)
