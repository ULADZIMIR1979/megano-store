from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import UserSerializer, UserRegistrationSerializer, UserPasswordSerializer
import json
import urllib.parse


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Отключает CSRF проверку для сессионной аутентификации
    """

    def enforce_csrf(self, request):
        return  # Не проверяем CSRF


User = get_user_model()


# users/views.py - обновленный SignInView

@method_decorator(csrf_exempt, name='dispatch')
class SignInView(APIView):
    """Аутентификация пользователя"""
    authentication_classes = []  # Не требуем аутентификации для входа
    permission_classes = []  # Не требуем прав для входа

    def post(self, request):
        """Основной метод входа (POST)"""
        print("🟢 POST запрос на /api/sign-in/")
        print(f"   Content-Type: {request.content_type}")
        print(f"   request.body: {request.body}")

        # Получаем данные из всех возможных источников
        username = None
        password = None

        # 1. Сначала пробуем распарсить body как JSON (фронтенд отправляет JSON с неверным content-type)
        try:
            import json
            body_str = request.body.decode('utf-8')
            if body_str and (body_str.startswith('{') or body_str.startswith('[')):
                json_data = json.loads(body_str)
                username = json_data.get('username') or json_data.get('login')
                password = json_data.get('password')
                if username and password:
                    print(f"   ✅ Распарсено как JSON: username={username}, password={password}")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"   Не JSON или ошибка парсинга JSON: {e}")

        # 2. Если не JSON, пробуем распарсить как form-data
        if not username and request.content_type == 'application/x-www-form-urlencoded':
            try:
                import urllib.parse
                body_str = request.body.decode('utf-8')
                parsed = urllib.parse.parse_qs(body_str)
                if parsed:
                    username = parsed.get('username', [''])[0] or parsed.get('login', [''])[0]
                    password = parsed.get('password', [''])[0]
                    print(f"   ✅ Распарсено как form-data: username={username}, password={password}")
            except Exception as e:
                print(f"   Ошибка парсинга form-data: {e}")

        # 3. Пробуем из request.data (для правильно отправленных запросов)
        if not username and hasattr(request, 'data') and request.data:
            username = request.data.get('username') or request.data.get('login')
            password = request.data.get('password')
            if username and password:
                print(f"   ✅ Из request.data: username={username}, password={password}")

        # 4. Проверяем query-параметры
        if not username and request.query_params:
            username = request.query_params.get('username') or request.query_params.get('login')
            password = request.query_params.get('password')
            if username and password:
                print(f"   ✅ Из query params: username={username}, password={password}")

        print(f"   👤 Итоговые данные - username='{username}', password='{password}'")

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                print(f"   ✅ Успешный вход для пользователя: {username}")
                return Response(status=status.HTTP_200_OK)
            else:
                print(f"   ❌ Ошибка аутентификации для: {username}")
                return Response(
                    {"error": "Неверные учетные данные"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            print("   ❌ Отсутствуют username или password")
            return Response(
                {"error": "Требуются username и password"},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class SignUpView(APIView):
    """Регистрация пользователя"""
    authentication_classes = []  # Не требуем аутентификации для регистрации
    permission_classes = []  # Не требуем прав для регистрации

    def post(self, request):
        print("🟢 POST запрос на /api/sign-up/")
        print(f"   Content-Type: {request.content_type}")

        # Получаем данные
        data = {}

        # 1. Пробуем из request.data (JSON)
        if hasattr(request, 'data') and request.data:
            data = request.data.copy()
            print(f"   Из request.data: {data}")

        # 2. Если нет данных, пробуем распарсить body как form-data
        elif request.content_type == 'application/x-www-form-urlencoded':
            try:
                body_str = request.body.decode('utf-8')
                parsed = urllib.parse.parse_qs(body_str)
                if parsed:
                    data = {
                        'name': parsed.get('name', [''])[0],
                        'username': parsed.get('username', [''])[0] or parsed.get('login', [''])[0],
                        'password': parsed.get('password', [''])[0],
                    }
                    print(f"   Распарсено из form-data: {data}")
            except Exception as e:
                print(f"   Ошибка парсинга form-data: {e}")

        # 3. Если данных все еще нет, проверяем query-параметры
        if not any(data.values()) and request.query_params:
            data = {
                'name': request.query_params.get('name', ''),
                'username': request.query_params.get('username') or request.query_params.get('login', ''),
                'password': request.query_params.get('password', ''),
            }
            print(f"   Из query params: {data}")

        print(f"   📝 Данные для регистрации: {data}")

        # Подготавливаем данные для сериализатора
        registration_data = {
            'name': data.get('name', ''),
            'username': data.get('username', ''),
            'password': data.get('password', ''),
            'password_confirm': data.get('password', ''),
        }

        serializer = UserRegistrationSerializer(data=registration_data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            print(f"   ✅ Успешная регистрация: {user.username}")
            return Response(status=status.HTTP_200_OK)
        else:
            print(f"   ❌ Ошибки валидации: {serializer.errors}")
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class SignOutView(APIView):
    """Выход пользователя"""
    # Временно убираем IsAuthenticated для отладки
    # permission_classes = [IsAuthenticated]
    permission_classes = []

    def post(self, request):
        # Проверяем, аутентифицирован ли пользователь
        if request.user.is_authenticated:
            logout(request)
            print("✅ Пользователь вышел из системы")
            return Response(status=status.HTTP_200_OK)
        else:
            # Если пользователь не аутентифицирован, все равно возвращаем 200
            # чтобы фронтенд мог очистить свои данные
            print("⚠ Выход без аутентификации")
            return Response(status=status.HTTP_200_OK)


class ProfileView(APIView):
    """Профиль пользователя"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfilePasswordView(APIView):
    """Изменение пароля пользователя"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserPasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileAvatarView(APIView):
    """Изменение аватара пользователя"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'avatar' in request.FILES:
            avatar = request.FILES['avatar']
            # Проверяем размер файла (не более 2 МБ)
            if avatar.size > 2 * 1024 * 1024:
                return Response({"error": "File size too large"}, status=status.HTTP_400_BAD_REQUEST)

            request.user.avatar = avatar
            request.user.save()
            serializer = UserSerializer(request.user, context={'request': request})
            return Response(serializer.data)
        return Response({"error": "No avatar provided"}, status=status.HTTP_400_BAD_REQUEST)
