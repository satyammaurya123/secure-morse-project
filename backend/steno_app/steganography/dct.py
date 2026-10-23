
import cv2
import numpy as np
from PIL import Image

class DCTSteganography:
    """
    Implements Discrete Cosine Transform (DCT) based Steganography.
    Hides data in the mid-frequency coefficients of 8x8 blocks.
    """
    
    @staticmethod
    def encode(image: Image.Image, message: str) -> Image.Image:
        # Convert PIL Image to OpenCV format (numpy array)
        # Handle RGB (3 channels) - We usually hide in the Blue channel or Luminance (Y)
        # For simplicity, let's use the Blue channel as it's less sensitive to human eye.
        img_array = np.array(image)
        
        # Ensure image is large enough
        # We need 1 block (8x8 pixels) per BIT.
        # Message: length + message + delimiter?
        # Let's stick to the delimiter approach for consistency with LSB.
        full_message = message + "#####"
        binary_message = ''.join(format(ord(char), '08b') for char in full_message)
        
        needed_blocks = len(binary_message)
        height, width, channels = img_array.shape
        
        # Calculate available bits (8 bits per block)
        h_blocks = height // 8
        w_blocks = width // 8
        total_blocks = h_blocks * w_blocks
        total_bits = total_blocks * 8
        
        if needed_blocks > total_bits:
            raise ValueError(f"Message too long. Need {needed_blocks} bits, have {total_bits}.")

        # Float conversion for DCT
        img_float = np.float32(img_array)
        
        # We will embed in the Blue channel (index 0 in BGR? PIL is RGB, so index 2 is Blue)
        # PIL: R=0, G=1, B=2
        channel_idx = 2 
        channel = img_float[:, :, channel_idx]
        
        msg_idx = 0
        msg_len = len(binary_message)

        for i in range(h_blocks):
            for j in range(w_blocks):
                if msg_idx < msg_len:
                    # Get 8x8 block
                    block = channel[i*8:(i+1)*8, j*8:(j+1)*8]
                    
                    # Apply DCT
                    dct_block = cv2.dct(block)
                    
                    # Embed 8 bits in 8 different mid-frequency coefficients
                    # (4,3), (5,2), (4,4), (3,4), (5,3), (3,5), (4,5), (5,4)
                    # We compare each with a neighboring coefficient.
                    
                    coef_pairs = [
                        ((5,2), (4,3)),
                        ((4,4), (3,4)),
                        ((5,3), (4,2)),
                        ((3,5), (2,6)),
                        ((4,5), (3,6)),
                        ((5,4), (6,3)),
                        ((6,2), (5,1)),
                        ((2,5), (1,6))
                    ]
                    
                    P = 25 # Strength of embedding
                    
                    for pair_idx in range(8):
                        if msg_idx >= msg_len:
                            break
                        
                        idx1, idx2 = coef_pairs[pair_idx]
                        v1 = dct_block[idx1]
                        v2 = dct_block[idx2]
                        bit = int(binary_message[msg_idx])
                        
                        if bit == 1:
                            if not (v1 > v2 + P):
                                v1 = v2 + P + 1
                        else: # bit == 0
                            if not (v1 < v2 - P):
                                v1 = v2 - P - 1
                                
                        dct_block[idx1] = v1
                        msg_idx += 1
                        
                    # Inverse DCT
                    # Code removed and placed in block above
                    
                    # Inverse DCT
                    idct_block = cv2.idct(dct_block)
                    
                    # Create a copy of the block to update
                    channel[i*8:(i+1)*8, j*8:(j+1)*8] = idct_block
                else:
                    break
            if msg_idx >= msg_len:
                break
                
        # Update the Blue channel
        img_float[:, :, channel_idx] = channel
        
        # Clip values to 0-255 and convert back to uint8
        img_out = np.clip(img_float, 0, 255)
        img_out = np.uint8(img_out)
        
        return Image.fromarray(img_out)

    @staticmethod
    def decode(image: Image.Image) -> str:
        img_array = np.array(image)
        img_float = np.float32(img_array)
        
        channel_idx = 2 # Blue
        channel = img_float[:, :, channel_idx]
        
        height, width = channel.shape
        h_blocks = height // 8
        w_blocks = width // 8
        
        bits = []
        
        num_blocks = h_blocks * w_blocks
        
        # We don't know the message length. We extract until delimiter.
        # This is risky with DCT as noise might create fake delimiters, but let's try.
        
        chars = []
        current_byte = ""
        
        for i in range(h_blocks):
            for j in range(w_blocks):
                block = channel[i*8:(i+1)*8, j*8:(j+1)*8]
                dct_block = cv2.dct(block)
                
                coef_pairs = [
                    ((5,2), (4,3)),
                    ((4,4), (3,4)),
                    ((5,3), (4,2)),
                    ((3,5), (2,6)),
                    ((4,5), (3,6)),
                    ((5,4), (6,3)),
                    ((6,2), (5,1)),
                    ((2,5), (1,6))
                ]
                
                for idx1, idx2 in coef_pairs:
                    v1 = dct_block[idx1]
                    v2 = dct_block[idx2]
                    
                    if v1 > v2:
                        bit = '1'
                    else:
                        bit = '0'
                        
                    current_byte += bit
                    
                    if len(current_byte) == 8:
                        char_code = int(current_byte, 2)
                        chars.append(chr(char_code))
                        current_byte = ""
                        
                        # Check delimiter '#####'
                        if len(chars) >= 5 and chars[-5:] == ['#', '#', '#', '#', '#']:
                            return ''.join(chars[:-5])
                        
        # If no delimiter found
        return ""
