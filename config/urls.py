from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def root_health_check(request):
    return Response({
        "status": "online",
        "message": "Mealy Backend API running",
        "endpoints": {
            "auth": "/api/auth/",
            "meals": "/api/meals/",
            "orders": "/api/orders/"
        }
    })


urlpatterns = [
    path('', root_health_check, name='root-health'),
    path('api/auth/', include('authentication.urls')),
    path('api/meals/', include('meals.urls')),
    path('api/orders/', include('orders.urls')),
]
