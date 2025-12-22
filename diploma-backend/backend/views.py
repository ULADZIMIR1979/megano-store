from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.views import APIView


@ensure_csrf_cookie
def get_csrf_token(request):
    """Представление для получения CSRF-токена"""
    token = get_token(request)
    return JsonResponse({'csrfToken': token})


class CSRFTokenView(APIView):
    """APIView для получения CSRF-токена"""
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        token = get_token(request)
        return JsonResponse({'csrfToken': token})

class DebugSignInView(APIView):
    """Отладочный endpoint для проверки данных входа"""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        print("=== DEBUG SIGN-IN ===")
        print(f"Content-Type: {request.content_type}")
        print(f"Headers:")
        for key, value in request.headers.items():
            print(f"  {key}: {value}")
        print(f"request.POST: {dict(request.POST)}")
        print(f"request.data: {request.data}")
        print(f"request.body: {request.body}")
        print(f"request.body decoded: {request.body.decode('utf-8', errors='ignore')}")
        print("=====================")

        return Response({
            'content_type': request.content_type,
            'headers': dict(request.headers),
            'post_data': dict(request.POST),
            'body_data': request.data,
            'body_raw': request.body.decode('utf-8', errors='ignore'),
        })