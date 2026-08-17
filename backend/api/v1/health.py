from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    db_ok = False
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception as e:
        pass

    return Response({
        "status": "ok",
        "database_connected": db_ok,
    })
