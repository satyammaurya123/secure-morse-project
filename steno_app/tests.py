from django.test import TestCase
from .utils import encrypt_message, decrypt_message, text_to_morse, morse_to_text, encode_image, decode_image
from PIL import Image
import os

class UtilsTestCase(TestCase):
    def test_encryption_decryption(self):
        key = "secret_key"
        message = "Hello World"
        encrypted = encrypt_message(message, key)
        decrypted = decrypt_message(encrypted, key)
        self.assertEqual(message, decrypted)

    def test_morse_conversion(self):
        text = "SOS"
        morse = text_to_morse(text)
        self.assertEqual(morse, "... --- ...")
        decoded_text = morse_to_text(morse)
        self.assertEqual(decoded_text, "SOS")

    def test_image_steganography(self):
        # Create a dummy image
        img = Image.new('RGB', (100, 100), color = 'white')
        message = "Hidden Message"
        
        encoded_img = encode_image(img, message)
        decoded_message = decode_image(encoded_img)
        
        self.assertEqual(message, decoded_message)
