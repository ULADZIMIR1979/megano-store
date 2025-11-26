from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import json
from shop.models import Product
from .models import Order, OrderProduct


@api_view(['GET', 'POST', 'DELETE'])
def basket(request):
    if request.method == 'GET':
        # Временная реализация - возвращаем пустую корзину
        return Response([])

    elif request.method == 'POST':
        # Добавление товара в корзину
        product_id = request.data.get('id')
        count = request.data.get('count', 1)

        try:
            product = Product.objects.get(id=product_id)
            # Здесь будет логика добавления в корзину (сессия или БД)
            return Response({'message': 'Товар добавлен в корзину'})
        except Product.DoesNotExist:
            return Response({'error': 'Товар не найден'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'DELETE':
        # Удаление товара из корзины
        return Response({'message': 'Товар удален из корзины'})


@api_view(['GET', 'POST'])
def orders_list(request):
    if request.method == 'GET':
        # Получение списка заказов
        orders = Order.objects.all()[:10]  # Ограничиваем для теста
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'createdAt': order.createdAt,
                'fullName': order.fullName,
                'email': order.email,
                'phone': order.phone,
                'deliveryType': order.deliveryType,
                'paymentType': order.paymentType,
                'totalCost': float(order.totalCost),
                'status': order.status,
                'city': order.city,
                'address': order.address,
            })
        return Response(orders_data)

    elif request.method == 'POST':
        # Создание заказа
        return Response({'orderId': 1})  # Временный ID


@api_view(['GET', 'POST'])
def order_detail(request, id):
    try:
        order = Order.objects.get(id=id)
        order_data = {
            'id': order.id,
            'createdAt': order.createdAt,
            'fullName': order.fullName,
            'email': order.email,
            'phone': order.phone,
            'deliveryType': order.deliveryType,
            'paymentType': order.paymentType,
            'totalCost': float(order.totalCost),
            'status': order.status,
            'city': order.city,
            'address': order.address,
            'products': []
        }

        for order_product in order.products.all():
            order_data['products'].append({
                'id': order_product.product.id,
                'title': order_product.product.title,
                'price': float(order_product.price),
                'count': order_product.count
            })

        return Response(order_data)

    except Order.DoesNotExist:
        return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)
