
from PIL import Image

class LSBSteganography:
    @staticmethod
    def encode(image: Image.Image, message: str) -> Image.Image:
        """
        Embeds a binary string into the LSB of an image.
        Appends a delimiter '#####' to denote end of message.
        """
        # Append delimiter
        full_message = message + "#####"
        # Convert message to binary (utf-8 bytes)
        full_message_bytes = full_message.encode('utf-8')
        binary_message = ''.join(format(b, '08b') for b in full_message_bytes)
        
        width, height = image.size
        max_bytes = (width * height * 3) // 8
        if len(full_message) > max_bytes:
            raise ValueError(f"Message too long for this image. Max chars: {max_bytes}")

        pixels = image.load()
        data_index = 0
        data_len = len(binary_message)
        
        for y in range(height):
            for x in range(width):
                if data_index < data_len:
                    pixel = list(pixels[x, y])
                    for i in range(3): # R, G, B
                        if data_index < data_len:
                            pixel[i] = (pixel[i] & ~1) | int(binary_message[data_index])
                            data_index += 1
                    pixels[x, y] = tuple(pixel)
                else:
                    break
            if data_index >= data_len:
                break
                
        return image

    @staticmethod
    def decode(image: Image.Image) -> str:
        """
        Extracts LSB data from image until delimiter '#####' is found.
        """
        pixels = image.load()
        width, height = image.size
        
        chars = []
        current_byte = ""
        
        for y in range(height):
            for x in range(width):
                pixel = pixels[x, y]
                for i in range(3):
                    current_byte += str(pixel[i] & 1)
                    
                    if len(current_byte) == 8:
                        byte_val = int(current_byte, 2)
                        chars.append(byte_val)
                        current_byte = ""
                        
                        # delimiter '#####' is 5 * 35 (in ascii '#' is 35. Wait, ord('#') is 35? No, it's 35 hex? ord('#') == 35 in dec)
                        # Let's check against bytes directly. '#' is 35 dec.
                        if len(chars) >= 5 and chars[-5:] == [35, 35, 35, 35, 35]:
                            # Decode bytes to string
                            return bytes(chars[:-5]).decode('utf-8', errors='replace')
                            
        return ""
