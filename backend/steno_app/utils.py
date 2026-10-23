def text_to_morse(text: str) -> str:
    """
    Converts text to a pseudo-Morse code binary mapping.
    Handles full UTF-8 encoded Unicode characters.
    '0' mapped to '.' and '1' mapped to '-'
    Bytes are separated by a space.
    """
    if not text:
        return ""
        
    bytes_data = text.encode('utf-8')
    morse_code = []
    
    for b in bytes_data:
        # Convert byte to 8-bit string
        bin_str = format(b, '08b')
        # Map 0 -> . and 1 -> -
        morse_byte = bin_str.replace('0', '.').replace('1', '-')
        morse_code.append(morse_byte)
        
    return ' '.join(morse_code)

def morse_to_text(morse_code: str) -> str:
    """
    Converts Pseudo-Morse binary space-separated string back to UTF-8 text.
    '.' mapped back to '0' and '-' mapped back to '1'.
    """
    if not morse_code:
        return ""
        
    morse_code = morse_code.strip()
    morse_bytes = morse_code.split(' ')
    byte_array = bytearray()
    
    for mb in morse_bytes:
        if not mb:
            continue
        # Map . -> 0 and - -> 1
        bin_str = mb.replace('.', '0').replace('-', '1')
        try:
            byte_val = int(bin_str, 2)
            byte_array.append(byte_val)
        except ValueError:
            # Handle malformed sequences gently
            pass
            
    try:
        return byte_array.decode('utf-8')
    except UnicodeDecodeError:
        # If decryption fails leading to bad UTF-8, return whatever decodable string we have or hex fallback
        return byte_array.decode('utf-8', errors='replace')
