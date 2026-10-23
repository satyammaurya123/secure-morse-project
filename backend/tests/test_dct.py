import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import numpy as np
from steno_app.steganography.dct import DCTSteganography

def run_test():
    # create dummy image
    img = Image.new('RGB', (100, 100), color='white')
    message = "TEST_MESSAGE_123"
    print(f"Original message: {message}")
    
    encoded = DCTSteganography.encode(img, message)
    print("Encoded successfully.")
    
    decoded = DCTSteganography.decode(encoded)
    print(f"Decoded message: {decoded}")
    
    if message == decoded:
        print("SUCCESS")
    else:
        print("FAILED")

if __name__ == "__main__":
    run_test()
