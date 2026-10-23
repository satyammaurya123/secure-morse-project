import logging
import hashlib
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from steno_app.models import AudioStegoLog
from PIL import Image

logger = logging.getLogger(__name__)

def api_root(request):
    logger.info("API root accessed")
    return JsonResponse({'status': 'SecureMorse API is running', 'version': '1.0'})

def extract_lsb_header(image_file):
    try:
        img = Image.open(image_file)
        if img.mode != 'RGB' and img.mode != 'RGBA':
            img = img.convert('RGB')
        
        pixels = img.load()
        width, height = img.size
        
        header_bytes = bytearray(37)
        bit_index = 0
        
        # We need 37 * 8 = 296 bits.
        for y in range(height):
            for x in range(width):
                pixel = pixels[x, y]
                for channel in range(3): # R, G, B
                    if bit_index >= 296:
                        break
                    
                    bit = pixel[channel] & 1
                    byte_index = bit_index // 8
                    bit_offset = 7 - (bit_index % 8)
                    
                    if bit:
                        header_bytes[byte_index] |= (1 << bit_offset)
                    
                    bit_index += 1
                
                if bit_index >= 296:
                    break
            if bit_index >= 296:
                break
        
        return header_bytes
    except Exception as e:
        logger.error(f"Error extracting LSB header: {e}")
        return None

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_audio_stego(request):
    image_hash = request.data.get('image_hash')
    version = request.data.get('version', 1)
    
    if not image_hash:
        return JsonResponse({'error': 'image_hash is required'}, status=400)
    
    # If the hash already exists, maybe the same user encoded it again or it's a re-upload.
    log, created = AudioStegoLog.objects.get_or_create(
        image_hash=image_hash,
        defaults={'uploader': request.user, 'version': int(version)}
    )
    
    return JsonResponse({'status': 'registered', 'id': log.id, 'created': created})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_audio_stego(request):
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'No image provided'}, status=400)
        
    image_file = request.FILES['image']
    
    file_content = image_file.read()
    image_hash = hashlib.sha256(file_content).hexdigest()
    image_file.seek(0)
    
    header = extract_lsb_header(image_file)
    if not header:
        return JsonResponse({'error': 'Failed to process image'}, status=400)
        
    magic = bytes(header[:4])
    if magic != b'AVT1':
        return JsonResponse({'error': 'No Hidden Data: Invalid Magic bytes', 'code': 'INVALID_MAGIC'}, status=400)
        
    version = header[4]
    
    # Check authorization
    try:
        log = AudioStegoLog.objects.get(image_hash=image_hash)
        if log.uploader != request.user:
            return JsonResponse({'error': 'Unauthorized: You are not the owner of this steganography image'}, status=403)
            
        log.extraction_attempts += 1
        log.save()
    except AudioStegoLog.DoesNotExist:
        # Strictly, if it's not in the DB, it's not authorized
        return JsonResponse({'error': 'Unauthorized: Image not registered in the system'}, status=403)

    return JsonResponse({
        'status': 'verified', 
        'version': version, 
        'message': 'Image verified and authorized for extraction.'
    })
