import os
import sys
import django
from PIL import Image

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secure_morse_project.settings')
django.setup()

from steno_app.utils import encrypt_message, decrypt_message, text_to_morse, morse_to_text, encode_image, decode_image

def test_logic():
    print("Testing Utils...")
    
    # Test 1: Encryption/Decryption
    key = "secret_key"
    message = "Hello World"
    encrypted = encrypt_message(message, key)
    print(f"Encrypted: {encrypted}")
    decrypted = decrypt_message(encrypted, key)
    print(f"Decrypted: {decrypted}")
    assert decrypted == message, "Decryption failed!"
    print("Encryption/Decryption Passed.")

    # Test 2: Morse Code
    morse = text_to_morse(message)
    print(f"Morse: {morse}")
    decoded_text = morse_to_text(morse)
    print(f"Decoded Morse: {decoded_text}")
    assert decoded_text == message.upper(), "Morse conversion failed!"
    print("Morse Code Passed.")

    # Test 3: Steganography
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color = 'red')
    encoded_img = encode_image(img, "Hidden Message")
    decoded_msg = decode_image(encoded_img)
    print(f"Decoded Stego: {decoded_msg}")
    assert decoded_msg == "Hidden Message", "Steganography failed!"
    print("Steganography Passed.")

if __name__ == "__main__":
    test_logic()
