
import os
import sys
import django
from django.conf import settings

# Setup Django environment to allow importing modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secure_morse_project.settings')
django.setup()

from steno_app.services.security_service import SecurityService
from steno_app.crypto.primitives import AESCipher
import binascii

def test_hybrid_flow():
    print("=== Testing Hybrid Crypto Flow ===")
    
    password = "strong_password_123"
    message = "Secret Mission: Launch at Midnight."
    print(f"Original Message: {message}")
    print(f"User Password: {password}")

    # 1. Generate keys
    print("\n1. Generating User Keys...")
    priv_pem, pub_pem = SecurityService.generate_user_keys()
    print("Keys Generated.")

    # 2. Encrypt Message (Hybrid)
    print("\n2. Encrypting Payload (Hybrid)...")
    hybrid_payload_hex = SecurityService.encrypt_payload(message, pub_pem, compress=True)
    print(f"Hybrid Payload Hex (First 50 chars): {hybrid_payload_hex[:50]}...")

    # 3. Encrypt Private Key with User's Password
    print("\n3. Encrypting Private Key with Password...")
    kek, salt = SecurityService.derive_encryption_key(password)
    enc_priv_ct, enc_priv_iv, enc_priv_tag = AESCipher.encrypt(priv_pem.encode('utf-8'), kek)
    
    # Pack: Salt (16) + IV (12) + Tag (16) + Ciphertext
    encrypted_priv_key_blob = salt + enc_priv_iv + enc_priv_tag + enc_priv_ct
    encrypted_priv_key_hex = binascii.hexlify(encrypted_priv_key_blob).decode('utf-8')
    print(f"Encrypted Private Key Blob Hex (First 50 chars): {encrypted_priv_key_hex[:50]}...")

    # 4. Combine (Simulate View Logic)
    print("\n4. Combining Payloads...")
    final_hex_payload = encrypted_priv_key_hex + ":::::" + hybrid_payload_hex
    print(f"Final Payload Length: {len(final_hex_payload)}")

    # --- Decryption ---
    print("\n=== Decryption Phase ===")
    
    # 5. Split
    print("5. Splitting Payload...")
    parts = final_hex_payload.split(":::::")
    if len(parts) != 2:
        print("FAILED: Payload split error.")
        return
    
    enc_priv_hex = parts[0]
    hybrid_hex = parts[1]

    # 6. Decrypt Private Key
    print("6. Decrypting Private Key...")
    try:
        enc_priv_blob = binascii.unhexlify(enc_priv_hex)
        salt_dec = enc_priv_blob[:16]
        iv_dec = enc_priv_blob[16:28]
        tag_dec = enc_priv_blob[28:44]
        ciphertext_dec = enc_priv_blob[44:]
        
        kek_dec, _ = SecurityService.derive_encryption_key(password, salt_dec)
        priv_pem_bytes = AESCipher.decrypt(ciphertext_dec, kek_dec, iv_dec, tag_dec)
        priv_pem_dec = priv_pem_bytes.decode('utf-8')
        print("Private Key Decrypted Successfully.")
        
        assert priv_pem == priv_pem_dec
        print("Key Integrity Verified.")
        
    except Exception as e:
        print(f"FAILED: Private Key Decryption Error: {e}")
        return

    # 7. Decrypt Hybrid Payload
    print("7. Decrypting Hybrid Payload...")
    try:
        decrypted_message = SecurityService.decrypt_payload(hybrid_hex, priv_pem_dec)
        print(f"Decrypted Message: {decrypted_message}")
        
        assert decrypted_message == message
        print("SUCCESS: Message Verified.")
        
    except Exception as e:
        print(f"FAILED: Hybrid Decryption Error: {e}")
        return

if __name__ == "__main__":
    test_hybrid_flow()
