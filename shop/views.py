from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Category, Product, Review, Tag
from .serializers import (CategorySerializer, ProductShortSerializer,
                          ProductFullSerializer, ReviewSerializer, TagSerializer)

@api_view(['GET'])
def categories_list(request):
    categories = Category.objects.filter(parent__isnull=True)
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def catalog(request):
    try:
        # Упрощенный запрос без фильтрации для теста
        products = Product.objects.filter(is_active=True)[:20]

        # Простой сериализатор без сложной логики
        items = []
        for product in products:
            items.append({
                'id': product.id,
                'category': product.category.id,
                'price': float(product.price),
                'count': product.count,
                'date': product.created_at.isoformat(),
                'title': product.title,
                'description': product.description,
                'freeDelivery': product.freeDelivery,
                'images': [{'src': '/static/frontend/assets/img/product.png', 'alt': product.title}],
                'tags': [{'id': tag.id, 'name': tag.name} for tag in product.tags.all()],
                'reviews': product.reviews.count(),
                'rating': float(product.rating)
            })

        return Response({
            'items': items,
            'currentPage': 1,
            'lastPage': 1
        })

    except Exception as e:
        print(f"Catalog error: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def popular_products(request):
    products = Product.objects.filter(is_active=True).order_by('-rating')[:8]
    # ИСПРАВЛЕНО: используем ProductShortSerializer
    serializer = ProductShortSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def limited_products(request):
    products = Product.objects.filter(limited=True, is_active=True)[:16]
    # ИСПРАВЛЕНО: используем ProductShortSerializer
    serializer = ProductShortSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def product_detail(request, id):
    try:
        product = Product.objects.get(id=id, is_active=True)
        # ИСПРАВЛЕНО: используем ProductFullSerializer для детальной страницы
        serializer = ProductFullSerializer(product)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def banners(request):
    # Возвращаем популярные товары как баннеры
    products = Product.objects.filter(is_active=True).order_by('-rating')[:3]
    # ИСПРАВЛЕНО: используем ProductShortSerializer
    serializer = ProductShortSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def sales(request):
    current_page = int(request.GET.get('currentPage', 1))
    limit = 20  # товаров на страницу

    # Для демо - возвращаем все товары как "распродажные"
    products = Product.objects.filter(is_active=True)

    # Пагинация
    start_index = (current_page - 1) * limit
    end_index = start_index + limit
    paginated_products = products[start_index:end_index]

    # ИСПРАВЛЕНО: используем ProductShortSerializer
    serializer = ProductShortSerializer(paginated_products, many=True)

    return Response({
        'items': serializer.data,
        'currentPage': current_page,
        'lastPage': (products.count() + limit - 1) // limit
    })

@api_view(['GET'])
def tags_list(request):
    tags = Tag.objects.all()
    serializer = TagSerializer(tags, many=True)
    return Response(serializer.data)
