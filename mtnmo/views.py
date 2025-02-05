from django.shortcuts import render
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

import logging

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'mtnmo/mtnmo.html')

# CSRF token endpoint for Flutter to fetch
@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    csrf_token = get_token(request)
    response = Response({'csrfToken': csrf_token})
    response["Access-Control-Allow-Origin"] = "https://www.teeket.app"
    response["Access-Control-Allow-Origin"] = "https://teeket-app-pink.vercel.app"
    response["Access-Control-Allow-Origin"] = "https://organizer.teeket.app"
    response["Access-Control-Allow-Origin"] = "https://triplib.teeket.app"
    return response