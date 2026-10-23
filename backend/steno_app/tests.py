from django.test import TestCase
from .utils import text_to_morse, morse_to_text
from .services.security_service import SecurityService
from .services.stego_service import StegoService
from PIL import Image
import binascii
import os

class UtilsTestCase(TestCase):
    def test_encryption_decryption(self):
        message = "Hello World"
        password = "test_password"
        
        # We test the SecurityService features instead of old encrypt_message
        kek, salt = SecurityService.derive_encryption_key(password)
        priv_pem, pub_pem = SecurityService.generate_user_keys()
        
        encrypted_hex = SecurityService.encrypt_payload(message, pub_pem, compress=False)
        decrypted = SecurityService.decrypt_payload(encrypted_hex, priv_pem)
        
        self.assertEqual(message, decrypted)

    def test_morse_conversion(self):
        text = "SOS 🌍! áéíóú"
        morse = text_to_morse(text)
        # We can't strictly compare output because encoding is dynamic, but we can verify round-trip
        decoded_text = morse_to_text(morse)
        self.assertEqual(decoded_text, text)

    def test_image_steganography_lsb(self):
        img = Image.new('RGB', (100, 100), color='white')
        message = "Hidden Message 🌍✨"
        
        encoded_img = StegoService.embed_message(img, message, 'LSB')
        decoded_message = StegoService.extract_message(encoded_img, 'LSB')
        
        self.assertEqual(message, decoded_message)
        
    def test_image_steganography_dct(self):
        img = Image.new('RGB', (100, 100), color='black')
        message = "DCT Test"
        
        encoded_img = StegoService.embed_message(img, message, 'DCT')
        decoded_message = StegoService.extract_message(encoded_img, 'DCT')
        
        self.assertEqual(message, decoded_message)
