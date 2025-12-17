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