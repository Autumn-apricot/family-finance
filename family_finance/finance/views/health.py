from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from finance.response import ok


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return ok({'status': 'ok', 'service': 'family_finance'})
