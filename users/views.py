from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from shop.models import User


@api_view(['POST'])
def sign_in(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return Response({'message': 'Успешный вход'})
    else:
        return Response({'error': 'Неверные учетные данные'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def sign_up(request):
    username = request.data.get('username')
    password = request.data.get('password')
    name = request.data.get('name')

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Пользователь уже существует'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        password=password,
        fullName=name
    )

    login(request, user)
    return Response({'message': 'Пользователь создан'})


@api_view(['POST'])
def sign_out(request):
    logout(request)
    return Response({'message': 'Выход выполнен'})
