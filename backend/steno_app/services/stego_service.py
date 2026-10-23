
from ..steganography.lsb import LSBSteganography
from ..steganography.dct import DCTSteganography
from PIL import Image

class StegoService:
    """
    Service for handling Image Steganography operations.
    Abstracts LSB / DCT selection.
    """
    
    @staticmethod
    def embed_message(image, message: str, method: str = 'LSB'):
        """
        Embeds a message into an image using the specified method.
        """
        if method == 'LSB':
            return LSBSteganography.encode(image, message)
        elif method == 'DCT':
            return DCTSteganography.encode(image, message)
        else:
            raise ValueError(f"Unknown steganography method: {method}")

    @staticmethod
    def extract_message(image, method: str = 'LSB') -> str:
        """
        Extracts a message from an image using the specified method.
        """
        if method == 'LSB':
            return LSBSteganography.decode(image)
        elif method == 'DCT':
            return DCTSteganography.decode(image)
        else:
            raise ValueError(f"Unknown steganography method: {method}")
