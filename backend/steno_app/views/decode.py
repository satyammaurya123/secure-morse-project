import logging
import binascii
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from PIL import Image

from ..serializers import DecodeRequestSerializer
from ..services.stego_service import StegoService
from ..crypto.primitives import AESCipher, KeyDerivation
from ..utils import morse_to_text

logger = logging.getLogger(__name__)

class DecodeView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    # A stego image doesn't record which method hid the data, so decoding tries each
    # one. LSB is the default first try: it is far cheaper than DCT's per-block scan.
    METHODS = ['LSB', 'DCT']

    @staticmethod
    def _extract_payload(img, method):
        """Return the hidden salt+nonce+tag+ciphertext bytes, or None when this
        method finds no well-formed payload in the image."""
        try:
            extracted_morse = StegoService.extract_message(img, method)
            if not extracted_morse:
                logger.info(f"{method}: no hidden message found")
                return None
            binary_payload = binascii.unhexlify(morse_to_text(extracted_morse))
        except Exception as e:
            logger.info(f"{method}: extraction failed: {str(e)}")
            return None
        if len(binary_payload) < 44:
            logger.info(f"{method}: payload too short ({len(binary_payload)} bytes)")
            return None
        return binary_payload

    def post(self, request):
        logger.info(f"Decode request received from user '{request.user.username}'")
        serializer = DecodeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Decode validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            secret_key = serializer.validated_data['secret_key']
            requested_method = serializer.validated_data.get('method', 'LSB')
            
            logger.debug(f"Requested method: {requested_method}")
            
            image_file = request.FILES.get('cover_media') or request.FILES.get('image')
            if not image_file:
                logger.error("Encoded media missing in decode request")
                return Response({"error": "Encoded media is required."}, status=status.HTTP_400_BAD_REQUEST)
                
            if requested_method not in self.METHODS:
                logger.error(f"Invalid method selected: {requested_method}")
                return Response({"error": "Invalid steganography method selected."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                img = Image.open(image_file)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                logger.debug("Image opened successfully for decoding")
            except Exception as e:
                logger.error(f"Failed to open image for decoding: {str(e)}")
                return Response({"error": "Unsupported image format."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Try the requested method first, then the rest: the image doesn't record
            # which method hid the data, and older clients always send 'LSB'.
            methods = [requested_method] + [m for m in self.METHODS if m != requested_method]
            binary_payload = None
            for method in methods:
                binary_payload = self._extract_payload(img, method)
                if binary_payload is not None:
                    # A well-formed payload means this is the right method, so a failed
                    # decryption below is a wrong password and other methods won't help.
                    logger.info(f"Hidden payload found using {method} method")
                    break
            if binary_payload is None:
                logger.warning("No hidden payload found with any method")
                return Response({"error": "Invalid key or corrupted image."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                salt = binary_payload[:16]
                nonce = binary_payload[16:28]
                tag = binary_payload[28:44]
                ciphertext = binary_payload[44:]

                key, _ = KeyDerivation.derive_key(secret_key, salt)
                decrypted_bytes = AESCipher.decrypt(ciphertext, key, nonce, tag)
                logger.debug("Decryption successful")
            except Exception as e:
                logger.error(f"Decryption process failed: {str(e)}")
                return Response({"error": "Invalid key or corrupted image."}, status=status.HTTP_400_BAD_REQUEST)
                
            try:
                separator_idx = decrypted_bytes.index(b':')
                secret_type = decrypted_bytes[:separator_idx].decode('utf-8')
                secret_data = decrypted_bytes[separator_idx+1:]
                logger.debug(f"Parsed secret_type: {secret_type}")
            except Exception as e:
                logger.warning(f"Could not parse secret type, defaulting to text. Error: {str(e)}")
                secret_type = "text"
                secret_data = decrypted_bytes
                
            response_data = {
                "success": "Image decoded successfully",
                "secret_type": secret_type
            }
            
            if secret_type == "text":
                response_data["message"] = secret_data.decode('utf-8', errors='replace')
            else:
                response_data["secret_file"] = binascii.b2a_base64(secret_data).decode('utf-8').strip()
                
            logger.info("Decode operation completed successfully")
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Unexpected error in DecodeView: {str(e)}")
            return Response({"error": "An internal error occurred during decoding."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
