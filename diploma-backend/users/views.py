from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from .serializers import UserSerializer, UserRegistrationSerializer
import json


User = get_user_model()



@method_decorator(csrf_protect, name='dispatch')
class SignInView(APIView):
    """Аутентификация пользователя"""
    def post(self, request):
        # Получаем параметры из query-параметров, как указано в swagger
        username = request.GET.get('username')
        password = request.GET.get('password')
        
        # Также поддерживаем параметры из тела запроса для обратной совместимости
        if not username:
            username = request.data.get('username')
        if not password:
            password = request.data.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                # Возвращаем пустой ответ как указано в swagger
                return Response(status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_protect, name='dispatch')
class SignUpView(APIView):
    """Регистрация пользователя"""
    def post(self, request):
        # Получаем параметры из query-параметров, как указано в swagger
        name = request.GET.get('name')
        username = request.GET.get('username')
        password = request.GET.get('password')
        
        # Также поддерживаем параметры из тела запроса для обратной совместимости
        if not name:
            name = request.data.get('name', '')
        if not username:
            username = request.data.get('username')
        if not password:
            password = request.data.get('password')
        
        # Подготавливаем данные для сериализатора
        data = {
            'username': username,
            'password': password
        }

        if name:
            data['first_name'] = name
        
        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            # Возвращаем пустой ответ как указано в swagger
            return Response(status=status.HTTP_200_OK)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SignOutView(APIView):
    """Выход пользователя"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logout(request)
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
        return Response(serializer.errors, status=status.HTTP_40_BAD_REQUEST)


class ProfilePasswordView(APIView):
    """Изменение пароля пользователя"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .serializers import UserPasswordSerializer
        serializer = UserPasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_40_BAD_REQUEST)


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
