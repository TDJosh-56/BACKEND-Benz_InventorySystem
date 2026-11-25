from django.conf import settings
from django.http import HttpResponse


class DevCorsMiddleware:
    """Development-only CORS middleware for Flutter Web."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            return self.get_response(request)

        if request.method == 'OPTIONS':
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = (
            'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        )
        response['Access-Control-Allow-Headers'] = (
            'Content-Type, Authorization'
        )

        return response