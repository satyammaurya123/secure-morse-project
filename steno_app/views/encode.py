import io
import os
import logging
import binascii
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from PIL import Image

from ..serializers import EncodeRequestSerializer
from ..services.stego_service import StegoService
from ..crypto.primitives import AESCipher, KeyDerivation
from ..utils import text_to_morse

logger = logging.getLogger(__name__)

class EncodeView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        logger.info(f"Encode request received from user '{request.user.username}'")
        serializer = EncodeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Encode validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            secret_key = serializer.validated_data['secret_key']
            method = serializer.validated_data.get('method', 'LSB')
            
            logger.debug(f"Using method: {method}")
            
            image_file = request.FILES.get('cover_media') or request.FILES.get('image')
            if not image_file:
                logger.error("Cover media missing in encode request")
                return Response({"error": "Cover media is required."}, status=status.HTTP_400_BAD_REQUEST)
                
            secret_type = serializer.validated_data.get('secret_type', 'text')
            logger.debug(f"Secret type: {secret_type}")
            
            message = ""
            if secret_type == 'text':
                message = request.POST.get('secret_text') or request.POST.get('message')
                if not message:
                    logger.error("Secret text missing in encode request")
                    return Response({"error": "Secret text is required for text payloads."}, status=status.HTTP_400_BAD_REQUEST)
                plaintext_bytes = message.encode('utf-8')
            else:
                secret_f = request.FILES.get('secret_file')
                if not secret_f:
                    logger.error(f"Secret file missing for generic {secret_type} payload in encode request")
                    return Response({"error": f"Secret file is required for {secret_type} payloads."}, status=status.HTTP_400_BAD_REQUEST)
                plaintext_bytes = secret_f.read()
                logger.debug(f"Read {len(plaintext_bytes)} bytes from secret file")

            if method not in ['LSB', 'DCT']:
                logger.error(f"Invalid method selected: {method}")
                return Response({"error": "Invalid steganography method selected."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                original_img = Image.open(image_file)
                if original_img.mode != 'RGB':
                    original_img = original_img.convert('RGB')
                logger.debug(f"Opened image, size: {original_img.size}, mode: {original_img.mode}")
            except Exception as e:
                logger.error(f"Failed to open image for encoding: {str(e)}")
                return Response({"error": "Unsupported image format."}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                full_plaintext = secret_type.encode('utf-8') + b":" + plaintext_bytes
                salt = os.urandom(16)
                key, _ = KeyDerivation.derive_key(secret_key, salt)
                ciphertext, nonce, tag = AESCipher.encrypt(full_plaintext, key)
                binary_payload = salt + nonce + tag + ciphertext
                hex_payload = binascii.hexlify(binary_payload).decode('utf-8')
                logger.debug("Encryption successful")
            except Exception as e:
                logger.error(f"Encryption process failed: {str(e)}")
                return Response({"error": "Encryption failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            morse_msg = text_to_morse(hex_payload)
            logger.debug(f"Converted hex payload to Morse code, length: {len(morse_msg)}")
            
            try:
                logger.info(f"Starting steganography embedding using {method} method")
                encoded_img = StegoService.embed_message(original_img, morse_msg, method)
                logger.info("Steganography embedding successful")
            except Exception as e:
                logger.error(f"Steganography embedding failed: {str(e)}")
                if "too long" in str(e).lower() or "need" in str(e).lower() or "capacity" in str(e).lower():
                    return Response({"error": "Image capacity insufficient."}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"error": "Encoding process failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            buffer = io.BytesIO()
            encoded_img.save(buffer, format="PNG")
            buffer.seek(0)
            encoded_base64 = binascii.b2a_base64(buffer.getvalue()).decode('utf-8').strip()
            
            media_type = image_file.content_type if hasattr(image_file, 'content_type') and image_file.content_type else "image/png"
            if not media_type.startswith('image/'):
                media_type = "image/png"

            logger.info("Encode operation completed successfully")
            return Response({
                "success": "Image encoded successfully",
                "encoded_media": encoded_base64,
                "encoded_image": encoded_base64,
                "media_type": media_type
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Unexpected error in EncodeView: {str(e)}")
            return Response({"error": "An internal error occurred during encoding."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
