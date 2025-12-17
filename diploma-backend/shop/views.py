from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Count
from django.core.paginator import Paginator
from .models import Product, Category, Tag, Review, Sale
from .serializers import (
    ProductShortSerializer, ProductFullSerializer,
    CategorySerializer, ReviewSerializer,
    TagSerializer, SaleSerializer
)
from users.serializers import UserSerializer, UserPasswordSerializer
from orders.models import Order, OrderProduct
from orders.serializers import OrderSerializer
from users.serializers import UserSerializer
from django.contrib.auth import get_user_model
import datetime


User = get_user_model()


class ProductListView(generics.ListAPIView):
    """Список продуктов с фильтрацией, сортировкой и пагинацией"""
    serializer_class = ProductShortSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True, available=True).prefetch_related(
            'images', 'tags', 'reviews', 'specifications'
        ).select_related('category')

        # Фильтрация
        name = self.request.query_params.get('filter[name]', None)
        min_price = self.request.query_params.get('filter[minPrice]', None)
        max_price = self.request.query_params.get('filter[maxPrice]', None)
        free_delivery = self.request.query_params.get('filter[freeDelivery]', None)
        available = self.request.query_params.get('filter[available]', None)
        category = self.request.query_params.get('category', None)
        tags = self.request.query_params.getlist('tags', None)

        if name:
            queryset = queryset.filter(title__icontains=name)
        if min_price:
            try:
                min_price = float(min_price)
                queryset = queryset.filter(price__gte=min_price)
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                max_price = float(max_price)
                queryset = queryset.filter(price__lte=max_price)
            except (ValueError, TypeError):
                pass
        if free_delivery == 'true':
            queryset = queryset.filter(freeDelivery=True)
        if available == 'false':
            queryset = queryset.filter(available=False)
        if category:
            try:
                category_id = int(category)
                queryset = queryset.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        if tags:
            for tag_id in tags:
                try:
                    tag_id = int(tag_id)
                    queryset = queryset.filter(tags__id=tag_id)
                except (ValueError, TypeError):
                    pass

        # Дополнительная фильтрация по характеристикам
        query_params = self.request.query_params
        for param, value in query_params.items():
            if param.startswith('filter[') and param not in [
                'filter[name]', 'filter[minPrice]', 'filter[maxPrice]',
                'filter[freeDelivery]', 'filter[available]'
            ]:
                spec_name = param[7:-1]
                queryset = queryset.filter(specifications__name__iexact=spec_name,
                                           specifications__value__icontains=value)

        # Сортировка
        sort = self.request.query_params.get('sort', 'date')
        sort_type = self.request.query_params.get('sortType', 'dec')

        order_field = {
            'date': 'created_at',
            'price': 'price',
            'name': 'title',
            'rating': 'rating',
            'reviews': 'reviews__count'
        }.get(sort, 'created_at')

        if sort == 'reviews':
            queryset = queryset.annotate(reviews_count=Count('reviews'))
            order_field = 'reviews_count'

        if sort_type == 'dec':
            order_field = f'-{order_field}'
        else:
            order_field = order_field

        queryset = queryset.order_by(order_field)

        # Пагинация
        page = self.request.query_params.get('currentPage', 1)
        limit = self.request.query_params.get('limit', 20)
        try:
            page = int(page)
            limit = int(limit)
        except (ValueError, TypeError):
            page = 1
            limit = 20

        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)

        return page_obj.object_list

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})

        page = int(request.query_params.get('currentPage', 1))
        limit = int(request.query_params.get('limit', 20))

        total_count = Product.objects.filter(is_active=True, available=True).count()
        last_page = (total_count + limit - 1) // limit

        # Вычисляем значения для отображения в пагинации
        start_item = (page - 1) * limit + 1
        end_item = min(page * limit, total_count) if total_count > 0 else 0

        return Response({
            'items': serializer.data,
            'currentPage': page,
            'lastPage': last_page,
            'totalItems': total_count,
            'itemsPerPage': limit,
            'startItem': start_item,
            'endItem': end_item
        })


class ProductDetailView(generics.RetrieveAPIView):
    """Детали продукта"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductFullSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'  # Указываем, что параметр URL называется 'id', а не 'pk'

    def get_serializer_context(self):
        return {'request': self.request}


class ProductPopularView(generics.ListAPIView):
    """Список популярных продуктов (по рейтингу)"""
    serializer_class = ProductShortSerializer
    permission_classes = [AllowAny]
    queryset = Product.objects.filter(is_active=True, available=True).order_by('-rating')[:8]

    def get_serializer_context(self):
        return {'request': self.request}


class ProductLimitedView(generics.ListAPIView):
    """Список продуктов ограниченного тиража"""
    serializer_class = ProductShortSerializer
    permission_classes = [AllowAny]
    queryset = Product.objects.filter(is_active=True, available=True, limited=True)[:16]

    def get_serializer_context(self):
        return {'request': self.request}


class ProductReviewView(APIView):
    """Создание отзыва к продукту"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, id):
        product = get_object_or_404(Product, id=id)
        
        # Подготовим данные для сериализатора
        data = {
            'product': product.id,
            'author': request.user.username if request.user.is_authenticated else 'Anonymous',
            'email': request.user.email if request.user.is_authenticated else '',
            'text': request.data.get('text'),
            'rate': request.data.get('rate')
        }
        
        serializer = ReviewSerializer(data=data)
        if serializer.is_valid():
            # Сохраняем отзыв
            review = serializer.save(product=product)
            # Возвращаем все отзывы для этого продукта, как указано в swagger
            all_reviews = Review.objects.filter(product=product)
            reviews_serializer = ReviewSerializer(all_reviews, many=True)
            return Response(reviews_serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SaleListView(APIView):
    """Список товаров со скидками"""
    permission_classes = [AllowAny]

    def get(self, request):
        current_date = datetime.datetime.now()
        queryset = Sale.objects.filter(
            dateFrom__lte=current_date,
            dateTo__gte=current_date
        ).prefetch_related('product__images')

        page = int(request.query_params.get('currentPage', 1))
        limit = 20
        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)

        serializer = SaleSerializer(page_obj.object_list, many=True, context={'request': request})

        current_date = datetime.datetime.now()
        total_count = Sale.objects.filter(
            dateFrom__lte=current_date,
            dateTo__gte=current_date
        ).count()
        last_page = (total_count + limit - 1) // limit

        return Response({
            'items': serializer.data,
            'currentPage': page,
            'lastPage': last_page
        })


class CategoryListView(generics.ListAPIView):
    """Список категорий"""
    queryset = Category.objects.filter(parent=None)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        return {'request': self.request}


class TagListView(generics.ListAPIView):
    """Список тегов"""
    serializer_class = TagSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        category_id = self.request.query_params.get('category', None)
        if category_id and category_id != 'NaN':
            try:
                category_id_int = int(category_id)
                return Tag.objects.filter(product__category_id=category_id_int).distinct()
            except (ValueError, TypeError):
                # Если не удается преобразовать в число, возвращаем все теги
                return Tag.objects.all()
        return Tag.objects.all()


class BannerListView(generics.ListAPIView):
    """Список товаров для баннера (топ 10 по рейтингу)"""
    serializer_class = ProductShortSerializer
    permission_classes = [AllowAny]
    queryset = Product.objects.filter(is_active=True, available=True).order_by('-rating')[:10]

    def get_serializer_context(self):
        return {'request': self.request}




class ProfileView(APIView):
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


def order_page(request):
    """Страница оформления заказа - создаем черновик заказа"""
    if request.method == 'GET':
        if not request.user.is_authenticated:
            # Для неавторизованных - форма авторизации
            return render(request, 'frontend/order.html')

        try:
            # Ищем не подтвержденный заказ пользователя
            draft_order = Order.objects.filter(
                user=request.user,
                status='created'
            ).order_by('-created_at').first()

            if draft_order:
                # Перенаправляем на существующий черновик
                return redirect(f'/orders/{draft_order.id}/')

        except Order.DoesNotExist:
            pass

        # Создаем новый черновик заказа
        try:
            # Получаем данные корзины
            from orders.views import BasketView as OrdersBasketView
            basket_view = OrdersBasketView()
            basket_view.request = request
            response = basket_view.get(request)
            basket_data = response.data

            items = basket_data.get('items', [])
            if not items:
                return redirect('/cart/')

            # Создаем черновик заказа
            user = request.user
            order = Order.objects.create(
                user=user,
                fullName=user.fullName if hasattr(user, 'fullName') and user.fullName else user.username,
                email=user.email or '',
                phone=user.phone if hasattr(user, 'phone') else '',
                deliveryType='ordinary',
                paymentType='online',
                status='draft',
                city='',
                address='',
                totalCost=0
            )

            # Добавляем товары
            total_cost = 0
            for item in items:
                try:
                    product = Product.objects.get(id=item['id'], is_active=True)
                    count = item.get('count', 1)

                    OrderProduct.objects.create(
                        order=order,
                        product=product,
                        count=count,
                        price=product.price
                    )
                    total_cost += product.price * count
                except (Product.DoesNotExist, KeyError):
                    continue

            # Обновляем стоимость
            order.totalCost = total_cost
            order.save()

            # Перенаправляем на страницу заказа с ID
            return redirect(f'/orders/{order.id}/')

        except Exception as e:
            print(f"Error creating draft order: {e}")
            # Если не получилось, показываем пустую форму
            return render(request, 'frontend/order.html')

    return redirect('/cart/')
