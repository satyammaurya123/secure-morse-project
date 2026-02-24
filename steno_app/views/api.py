import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def api_root(request):
    logger.info("API root accessed")
    return JsonResponse({'status': 'SecureMorse API is running', 'version': '1.0'})
