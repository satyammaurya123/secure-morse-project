import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from PIL import Image
import binascii

# Morse Code Dictionary
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 
    'Z': '--..', '1': '.----', '2': '..---', '3': '...--', 
    '4': '....-', '5': '.....', '6': '-....', '7': '--...', 
    '8': '---..', '9': '----.', '0': '-----', ',': '--..--', 
    '.': '.-.-.-', '?': '..--..', '/': '-..-.', '-': '-....-', 
    '(': '-.--.', ')': '-.--.-', ' ': '/'
}

REVERSE_MORSE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}

def encrypt_message(plaintext, key):
    """
    Encrypts plaintext using AES-256 CBC mode.
    Returns value as a hex string prefixed with the IV.
    """
    # Ensure key is 32 bytes (256 bits)
    # Pad with spaces or truncate if needed, but ideally user provides good key.
    # For simplicity, we'll hash the key to get 32 bytes or just pad.
    # Let's use SHA-256 on the key to get a consistent 32-byte key
    from Crypto.Hash import SHA256
    h = SHA256.new()
    h.update(key.encode('utf-8'))
    key_bytes = h.digest()
    
    iv = get_random_bytes(16)
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    encrypted_bytes = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    # Combine IV and encrypted data, then convert to hex
    return binascii.hexlify(iv + encrypted_bytes).decode('utf-8').upper()

def decrypt_message(ciphertext_hex, key):
    """
    Decrypts a hex string (IV + ciphertext) using AES-256 CBC mode.
    """
    try:
        data_bytes = binascii.unhexlify(ciphertext_hex)
        iv = data_bytes[:16]
        encrypted_bytes = data_bytes[16:]
        
        from Crypto.Hash import SHA256
        h = SHA256.new()
        h.update(key.encode('utf-8'))
        key_bytes = h.digest()
        
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
        return decrypted_bytes.decode('utf-8')
    except (ValueError, KeyError, binascii.Error) as e:
        return f"Decryption Failed: {str(e)}"

def text_to_morse(text):
    """
    Converts text to Morse code. 
    Accepts alphanumeric characters and basic punctuation.
    """
    text = str(text).upper()
    morse_code = []
    for char in text:
        if char in MORSE_CODE_DICT:
            morse_code.append(MORSE_CODE_DICT[char])
        else:
            # For non-supported chars, we skip or use '?'
            # Since encryption produces Hex (0-9, A-F), this is safe.
            pass 
    return ' '.join(morse_code)

def morse_to_text(morse_code):
    """
    Converts Morse code string back to text.
    """
    if not morse_code:
        return ""
        
    chars = morse_code.strip().split(' ')
    text = []
    for char in chars:
        if char in REVERSE_MORSE_DICT:
            text.append(REVERSE_MORSE_DICT[char])
        elif char == '':
            pass
        else:
            text.append('?') # Unknown char
    return ''.join(text)

def encode_image(image, message):
    """
    Embeds a message string into the LSB of an image.
    Appends a delimiter '#####' to denote end of message.
    """
    # Append delimiter
    full_message = message + "#####"
    # Convert message to binary (8-bit ASCII)
    binary_message = ''.join(format(ord(char), '08b') for char in full_message)
    
    # Check if image can hold the data
    width, height = image.size
    max_bytes = (width * height * 3) // 8
    if len(full_message) > max_bytes:
        raise ValueError(f"Message too long for this image. Max chars: {max_bytes}")

    pixels = image.load()
    data_index: int = 0
    data_len = len(binary_message)
    
    # We need to iterate and modifying pixels. 
    # To save modified image, we just modify 'pixels' in place (it's a view).
    
    for y in range(height):
        for x in range(width):
            if data_index < data_len:
                pixel = list(pixels[x, y])
                # Modify LSB of Red, Green, Blue
                for i in range(3): # R, G, B
                    if data_index < data_len:
                        # Clear LSB and set to bit
                        pixel[i] = (pixel[i] & ~1) | int(binary_message[data_index])
                        data_index += 1
                pixels[x, y] = tuple(pixel)
            else:
                break
        if data_index >= data_len:
            break
            
    return image

def decode_image(image):
    """
    Extracts LSB data from image until delimiter '#####' is found.
    Usage:
        msg = decode_image(img)
    """
    pixels = image.load()
    width, height = image.size
    
    chars: list[str] = []
    current_byte: str = ""
    
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            for i in range(3): # R, G, B
                current_byte += str(pixel[i] & 1)
                
                if len(current_byte) == 8:
                    char = chr(int(current_byte, 2))
                    chars.append(char)
                    current_byte = ""
                    
                    # Check delimiter
                    if len(chars) >= 5 and chars[-1] == '#' and chars[-2] == '#' and chars[-3] == '#' and chars[-4] == '#' and chars[-5] == '#':
                        # Found delimiter. Remove last 5 chars and return.
                        # Using pop() loop to avoid list slicing error in strict type checkers.
                        for _ in range(5):
                            chars.pop()
                        return ''.join(chars)
                        
    # If no delimiter found, return empty string or whatever was decoded?
    # Usually better to return empty if integrity check fails, but for now empty is safe.
    return ""
