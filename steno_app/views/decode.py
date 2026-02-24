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

    def post(self, request):
        logger.info(f"Decode request received from user '{request.user.username}'")
        serializer = DecodeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Decode validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            secret_key = serializer.validated_data['secret_key']
            method = serializer.validated_data.get('method', 'LSB')
            
            logger.debug(f"Using method: {method}")
            
            image_file = request.FILES.get('cover_media') or request.FILES.get('image')
            if not image_file:
                logger.error("Encoded media missing in decode request")
                return Response({"error": "Encoded media is required."}, status=status.HTTP_400_BAD_REQUEST)
                
            if method not in ['LSB', 'DCT']:
                logger.error(f"Invalid method selected: {method}")
                return Response({"error": "Invalid steganography method selected."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                img = Image.open(image_file)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                logger.debug("Image opened successfully for decoding")
            except Exception as e:
                logger.error(f"Failed to open image for decoding: {str(e)}")
                return Response({"error": "Unsupported image format."}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                logger.info(f"Extracting message using {method} method")
                extracted_morse = StegoService.extract_message(img, method)
                if not extracted_morse:
                    logger.warning("No Morse message could be extracted (likely corrupted or wrong method/key)")
                    return Response({"error": "Invalid key or corrupted image."}, status=status.HTTP_400_BAD_REQUEST)
                logger.debug("Morse code extracted successfully")
            except Exception as e:
                logger.error(f"Message extraction failed: {str(e)}")
                return Response({"error": "Invalid key or corrupted image."}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                hex_payload = morse_to_text(extracted_morse)
                binary_payload = binascii.unhexlify(hex_payload)
                logger.debug("Morse converted back to binary payload successfully")
            except Exception as e:
                logger.error(f"Morse conversion/unhexlify failed: {str(e)}")
                return Response({"error": "Invalid key or corrupted image."}, status=status.HTTP_400_BAD_REQUEST)
                
            try:
                if len(binary_payload) < 44:
                    logger.warning(f"Binary payload too short: {len(binary_payload)} bytes")
                    raise ValueError("Payload too short.")
                    
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
