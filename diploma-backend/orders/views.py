from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from products.models import Product
import json

User = get_user_model()


# ========== HELPER FUNCTIONS ==========
def calculate_delivery_price(delivery_type, total_cost):
    """Рассчитать стоимость доставки"""
    if delivery_type == 'express':
        return 500
    elif total_cost < 2000:
        return 200
    return 0


def create_product_data(product, count, price=None):
    """Создать данные товара для ответа"""
    if price is None:
        price = product.price

    # Используем предзагруженные связанные объекты, если они доступны
    try:
        # Проверяем, были ли предзагружены изображения
        images = product.images.all()
    except AttributeError:
        # Если нет, загружаем их
        images = product.images.all()

    try:
        # Проверяем, были ли предзагружены теги
        tags = product.tags.all()
    except AttributeError:
        # Если нет, загружаем их
        tags = product.tags.all()

    return {
        'id': product.id,
        'category': product.category.id,
        'price': float(price),
        'count': count,
        'date': product.created_at.strftime("%a %b %d %Y %H:%M:%S GMT%z"),
        'title': product.title,
        'description': product.description,
        'freeDelivery': product.freeDelivery,
        'images': [
            {
                'src': f'/media/{img.src}' if img.src else '/static/frontend/assets/img/product.png',
                'alt': img.alt
            }
            for img in images
        ],
        'tags': [tag.id for tag in tags],
        'reviews': product.reviews.count(),
        'rating': float(product.rating)
    }


def check_order_access(request, order):
    """Проверить доступ пользователя к заказу"""
    if request.user.is_staff:
        return True
    return order.user == request.user


def check_basket_empty(user):
    """Проверить, пуста ли корзина"""
    try:
        basket_order = Order.objects.get(user=user, status='accepted')
        return OrderProduct.objects.filter(order=basket_order).count() == 0
    except Order.DoesNotExist:
        return True


def create_order_from_basket(user):
    """Создать заказ из корзины пользователя"""
    try:
        basket_order = Order.objects.get(user=user, status='accepted')
        basket_items = OrderProduct.objects.filter(order=basket_order)

        if basket_items.count() == 0:
            return None

        # Проверяем, не был ли уже создан заказ из этой корзины
        existing_order = Order.objects.filter(
            user=user,
            status='created',
            createdAt__gte=basket_order.createdAt
        ).exists()

        if existing_order:
            # Если заказ уже был создан, возвращаем последний созданный заказ
            return Order.objects.filter(user=user).exclude(status='accepted').order_by('-createdAt').first()

        # Создаем новый заказ со статусом 'created' с пустыми полями для заполнения пользователем
        order = Order.objects.create(
            user=user,
            fullName='',
            email='',
            phone='',
            deliveryType='ordinary',
            paymentType='online',
            status='created',
            city='',
            address=''
        )

        # Переносим товары из корзины
        total_cost = 0
        for item in basket_items:
            OrderProduct.objects.create(
                order=order,
                product=item.product,
                count=item.count,
                price=item.price
            )
            total_cost += item.price * item.count

        # Рассчитываем доставку
        delivery_price = calculate_delivery_price(order.deliveryType, total_cost)
        order.totalCost = total_cost + delivery_price
        order.save()

        # Удаляем корзину
        basket_order.delete()

        return order

    except Order.DoesNotExist:
        return None


def get_basket_items_for_user(request):
    """Получить элементы корзины для пользователя (авторизованного или анонимного)"""
    if request.user.is_authenticated:
        try:
            basket_order = Order.objects.get(user=request.user, status='accepted')
            order_products = OrderProduct.objects.filter(order=basket_order).select_related('product').prefetch_related(
                'product__images', 'product__tags'
            )

            basket_items = []
            for op in order_products:
                basket_items.append(create_product_data(op.product, op.count, op.price))
            return basket_items
        except Order.DoesNotExist:
            return []
    else:
        # Для анонимных пользователей используем сессию
        basket = request.session.get('basket', [])
        basket_items = []

        for item in basket:
            try:
                product = Product.objects.get(id=item['id'])
                basket_items.append(create_product_data(product, item['count']))
            except Product.DoesNotExist:
                continue

        return basket_items


# ========== VIEW FUNCTIONS ==========
def create_order_from_cart(request):
    """Отображение страницы оформления заказа при GET-запросе"""
    print(f"DEBUG: Loading order page. Method: {request.method}")

    # Проверяем авторизацию
    if not request.user.is_authenticated:
        return redirect('/sign-in/')

    print(f"DEBUG: User: {request.user}")

    # Проверяем, есть ли товары в корзине
    if check_basket_empty(request.user):
        print("DEBUG: Basket is empty, redirecting to /cart/")
        return redirect('/cart/')

    # Показываем форму оформления заказа
    return render(request, 'frontend/order.html')


def create_order_and_redirect(request):
    """Создать заказ из корзины и перенаправить на страницу заказа"""
    if not request.user.is_authenticated:
        return redirect('/sign-in/')

    order = create_order_from_basket(request.user)

    if order:
        return redirect(f'/orders/{order.id}/')
    else:
        return redirect('/cart/')


def redirect_to_latest_order(request):
    """Перенаправление на последний заказ пользователя"""
    if request.user.is_authenticated:
        latest_order = Order.objects.filter(user=request.user).order_by('-createdAt').first()
        if latest_order:
            try:
                order_id = int(latest_order.id)
                return redirect(f'/orders/{order_id}/')
            except (ValueError, TypeError):
                pass

    return redirect('/cart/')


def order_page_view(request):
    """Страница оформления нового заказа"""
    if not request.user.is_authenticated:
        return redirect('/sign-in/')

    # Проверяем корзину
    if check_basket_empty(request.user):
        return redirect('/cart/')

    return render(request, 'frontend/order.html')


def order_detail_page(request, id):
    """Страница существующего заказа"""
    if request.method == 'POST':
        from django.http import JsonResponse
        return JsonResponse({"error": "Use /api/orders/{id}/ for API requests"}, status=405)

    if not request.user.is_authenticated:
        return redirect('/sign-in/')

    try:
        order = Order.objects.get(id=id, user=request.user)
        return render(request, 'frontend/oneorder.html')
    except Order.DoesNotExist:
        return redirect('/cart/')


# ========== API VIEWS ==========
class ActiveOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /orders/ - Список заказов пользователя"""
        orders = Order.objects.filter(user=request.user).exclude(status='accepted').order_by('-createdAt')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, order=None):
        """POST /orders/ - Создание заказа из корзины"""
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        order = create_order_from_basket(request.user)

        if order:
            return Response({"orderId": order.id}, status=status.HTTP_201_CREATED)
        elif order is None:
            return Response({"error": "No basket found"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Basket is empty"}, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    """Работа с конкретным заказом"""
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        """GET: Получение данных заказа для отображения"""

        try:
            id = int(id)
        except (ValueError, TypeError):
            return Response({"error": "Invalid order ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем заказ
        order = get_object_or_404(Order, id=id)

        # Проверяем доступ
        if not check_order_access(request, order):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        # Получаем данные товаров
        products_data = self._get_products_data(order)

        # Подготавливаем данные для фронтенда
        response_data = {
            "id": order.id,
            "orderId": order.id,
            "createdAt": order.createdAt,
            "fullName": order.fullName,
            "email": order.email,
            "phone": order.phone,
            "deliveryType": order.get_deliveryType_display(),
            "paymentType": order.get_paymentType_display(),
            "city": order.city,
            "address": order.address,
            "status": order.get_status_display(),
            "totalCost": float(order.totalCost),
            "products": products_data,
            "comment": order.comment or ""
        }

        return Response(response_data)

    def post(self, request, id):
        """POST: Подтверждение заказа (отправка данных формы)"""

        try:
            id = int(id)
        except (ValueError, TypeError):
            return Response({"error": "Invalid order ID"}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=id)

        # Проверяем доступ
        if not check_order_access(request, order):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data

        # Проверяем структуру данных
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value} (тип: {type(value)})")
        else:
            print(f"Данные в другом формате: {type(data)}")

        # Получаем данные из Vue объекта
        full_name = data.get('fullName')
        email = data.get('email')
        phone = data.get('phone')
        city = data.get('city')
        address = data.get('address')
        delivery_type = data.get('deliveryType')
        payment_type = data.get('paymentType')

        # Обновляем поля заказа
        if full_name is not None:
            order.fullName = full_name

        if email is not None:
            order.email = email

        if phone is not None:
            order.phone = phone

        if city is not None:
            order.city = city

        if address is not None:
            order.address = address

        # КРИТИЧЕСКАЯ ЧАСТЬ: Обработка deliveryType
        if delivery_type is None or delivery_type == '':
            if 'delivery' in data:
                delivery_type = data.get('delivery')
            elif order.deliveryType:
                delivery_type = order.deliveryType
            else:
                delivery_type = 'ordinary'

        # Обрабатываем значение delivery_type
        if delivery_type:
            if delivery_type == 'free':
                delivery_type = 'ordinary'

            if delivery_type in ['ordinary', 'express']:
                order.deliveryType = delivery_type
            else:
                order.deliveryType = 'ordinary'

        # КРИТИЧЕСКАЯ ЧАСТЬ: Обработка paymentType
        if payment_type is None or payment_type == '':
            if 'pay' in data:
                payment_type = data.get('pay')
            elif order.paymentType:
                payment_type = order.paymentType
            else:
                payment_type = 'online'

        # Обрабатываем значение payment_type
        if payment_type:
            if payment_type == 'random':
                payment_type = 'someone'

            if payment_type in ['online', 'someone']:
                order.paymentType = payment_type
            else:
                order.paymentType = 'online'

        # Пересчитываем стоимость
        order_products = order.products.all()
        total_product_cost = sum(float(item.price) * item.count for item in order_products)

        # Рассчитываем доставку
        delivery_price = calculate_delivery_price(order.deliveryType, total_product_cost)
        order.totalCost = total_product_cost + delivery_price

        # Устанавливаем статус
        order.status = 'confirmed'
        order.save()

        return Response({
            "orderId": order.id
        })

    def _get_products_data(self, order):
        """Получить данные товаров заказа"""

        order_products = order.products.select_related('product').prefetch_related(
            'product__images'
        ).all()

        products_data = []

        for op in order_products:
            product = op.product
            product_data = {
                'id': product.id,
                'title': product.title,
                'description': product.description,
                'price': float(op.price),
                'count': op.count,
                'date': product.created_at.strftime("%a %b %d %Y %H:%M:%S GMT%z"),
                'images': [
                    {
                        'src': image.src.url if image.src else '/static/frontend/assets/img/product.png',
                        'alt': image.alt or product.title
                    }
                    for image in product.images.all()[:1]
                ],
                'shortDescription': product.description[:100] + '...' if product.description else ''
            }
            products_data.append(product_data)

        return products_data


class OrderDetailUndefinedView(APIView):
    """Обработка запроса к заказу с undefined ID"""

    def get(self, request):
        return Response({
            "error": "Invalid order ID",
            "message": "Order ID cannot be undefined"
        }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        return Response({
            "error": "Invalid order ID",
            "message": "Order ID cannot be undefined"
        }, status=status.HTTP_400_BAD_REQUEST)


class BasketView(APIView):
    """Работа с корзиной"""

    def get(self, request):
        return Response(get_basket_items_for_user(request))

    def post(self, request):
        product_id = request.data.get('id')
        count = int(request.data.get('count', 1))
        product = get_object_or_404(Product, id=product_id)

        if request.user.is_authenticated:
            basket_order, created = Order.objects.get_or_create(
                user=request.user,
                status='accepted'
            )

            order_product, created = OrderProduct.objects.get_or_create(
                order=basket_order,
                product=product,
                defaults={'count': count, 'price': product.price}
            )

            if not created:
                order_product.count += count
                order_product.save()
            else:
                order_product.price = product.price
                order_product.save()

            return Response(get_basket_items_for_user(request))
        else:
            basket = request.session.get('basket', [])
            item_exists = False

            for item in basket:
                if item['id'] == product_id:
                    item['count'] += count
                    item_exists = True
                    break

            if not item_exists:
                basket.append({'id': product_id, 'count': count})

            request.session['basket'] = basket
            return Response(get_basket_items_for_user(request))

    def delete(self, request):
        """
        Удаление товара из корзины
        Обрабатывает строку JSON от фронтенда
        """

        if request.content_type == 'text/plain;charset=UTF-8' and request.body:
            try:
                body_str = request.body.decode('utf-8')
                data = json.loads(body_str)
                product_id = data.get('id')
                count = int(data.get('count', 1))
            except json.JSONDecodeError as e:
                return Response(
                    {"error": "Invalid JSON format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                print(f"Error: {e}")
                return Response(
                    {"error": "Error processing request"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            product_id = request.data.get('id')
            count = int(request.data.get('count', 1))

        # Проверяем, что получили id
        if not product_id:
            print(f"No product_id found. Request data: {request.data}")
            return Response(
                {"error": "Product ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.is_authenticated:
            try:
                basket_order = Order.objects.get(user=request.user, status='accepted')
                order_product = OrderProduct.objects.get(order=basket_order, product_id=product_id)

                if order_product.count > count:
                    order_product.count -= count
                    order_product.save()
                else:
                    order_product.delete()

                return Response(get_basket_items_for_user(request))
            except (Order.DoesNotExist, OrderProduct.DoesNotExist):
                return Response([])
        else:
            basket = request.session.get('basket', [])
            new_basket = []

            for item in basket:
                if item['id'] == product_id:
                    if item['count'] > count:
                        item['count'] -= count
                        new_basket.append(item)
                else:
                    new_basket.append(item)

            request.session['basket'] = new_basket
            return Response(get_basket_items_for_user(request))


class PaymentView(APIView):
    """Обработка оплаты"""
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            id = int(id)
        except (ValueError, TypeError):
            return Response({"error": "Invalid order ID"}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=id)

        # Проверяем, что пользователь имеет доступ к заказу
        if not check_order_access(request, order):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        # Получаем данные для оплаты
        payment_data = request.data

        # Проверяем номер карты/счета
        number = payment_data.get('number', '')
        name = payment_data.get('name', '')
        month = payment_data.get('month', '')
        year = payment_data.get('year', '')
        code = payment_data.get('code', '')

        # Создаем запись о платеже
        payment_obj = Payment.objects.create(
            order=order,
            number=number,
            name=name,
            month=month,
            year=year,
            code=code
        )

        try:
            if number:
                # Проверяем, что номер четный и не заканчивается на 0
                number_int = int(number.replace(' ', ''))
                if number_int % 2 != 0 or number_int % 10 == 0:
                    # Случайная ошибка оплаты
                    import random
                    errors = [
                        "Card number validation failed",
                        "Payment declined by bank",
                        "Insufficient funds",
                        "Card expired"
                    ]
                    error_message = random.choice(errors)
                    order.status = 'cancelled'
                    order.save()
                    payment_obj.status = 'failed'
                    payment_obj.save()
                    return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

            # Успешная оплата
            order.status = 'paid'
            order.save()
            payment_obj.status = 'completed'
            payment_obj.save()
            return Response({"result": "Payment successful"})

        except (ValueError, AttributeError):
            payment_obj.status = 'failed'
            payment_obj.save()
            return Response({"error": "Invalid number format"}, status=status.HTTP_400_BAD_REQUEST)


class PaymentStatusView(APIView):
    """Получение статуса оплаты заказа"""
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            id = int(id)
        except (ValueError, TypeError):
            return Response({"error": "Invalid order ID"}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=id)

        # Проверяем, что пользователь имеет доступ к заказу
        if not check_order_access(request, order):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            "status": order.status,
            "error": None
        })

from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .models import Order, OrderProduct, Cart, Payment
from products.models import Product
from .serializers import OrderSerializer, PaymentSerializer
import json

User = get_user_model()


# ========== HELPER FUNCTIONS ==========
def calculate_delivery_price(delivery_type, total_cost):
    """Рассчитать стоимость доставки"""
    if delivery_type == 'express':
        return 500
    elif total_cost < 2000:
        return 200
    return 0


def create_product_data(product, count, price=None):
    """Создать данные товара для ответа"""
    if price is None:
        price = product.price

    return {
        'id': product.id,
        'category': product.category.id,
        'price': float(price),
        'count': count,
        'date': product.created_at.strftime("%a %b %d %Y %H:%M:%S GMT%z"),
        'title': product.title,
        'description': product.description,
        'freeDelivery': product.freeDelivery,
        'images': [
            {
                'src': f'/media/{img.src}' if img.src else '/static/frontend/assets/img/product.png',
                'alt': img.alt
            }
            for img in product.images.all()
        ],
        'tags': [tag.id for tag in product.tags.all()],
        'reviews': product.reviews.count(),
        'rating': float(product.rating)
    }


def check_order_access(request, order):
    """Проверить доступ пользователя к заказу"""
    if request.user.is_staff:
        return True
    return order.user == request.user


def check_basket_empty(user):
    """Проверить, пуста ли корзина"""
    try:
        basket_order = Order.objects.get(user=user, status='accepted')
        return OrderProduct.objects.filter(order=basket_order).count() == 0
    except Order.DoesNotExist:
        return True


def create_order_from_basket(user):
    """Создать заказ из корзины пользователя"""
    try:
        basket_order = Order.objects.get(user=user, status='accepted')
        basket_items = OrderProduct.objects.filter(order=basket_order)

        if basket_items.count() == 0:
            return None

        # Проверяем, не был ли уже создан заказ из этой корзины
        existing_order = Order.objects.filter(
            user=user,
            status='created',
            createdAt__gte=basket_order.createdAt
        ).exists()

        if existing_order:
            # Если заказ уже был создан, возвращаем последний созданный заказ
            return Order.objects.filter(user=user).exclude(status='accepted').order_by('-createdAt').first()

        # Создаем новый заказ со статусом 'created' с пустыми полями для заполнения пользователем
        order = Order.objects.create(
            user=user,
            fullName='',
            email='',
            phone='',
            deliveryType='ordinary',
            paymentType='online',
            status='created',
            city='',
            address=''
        )

        # Переносим товары из корзины
        total_cost = 0
        for item in basket_items:
            OrderProduct.objects.create(
                order=order,
                product=item.product,
                count=item.count,
                price=item.price
            )
            total_cost += item.price * item.count

        # Рассчитываем доставку
        delivery_price = calculate_delivery_price(order.deliveryType, total_cost)
        order.totalCost = total_cost + delivery_price
        order.save()

        # Удаляем корзину
        basket_order.delete()

        return order

    except Order.DoesNotExist:
        return None


def get_basket_items_for_user(request):
    """Получить элементы корзины для пользователя (авторизованного или анонимного)"""
    if request.user.is_authenticated:
        try:
            basket_order = Order.objects.get(user=request.user, status='accepted')
            order_products = OrderProduct.objects.filter(
                order=basket_order
            ).select_related('product').prefetch_related(
                'product__images', 'product__tags', 'product__category'
            )

            basket_items = []
            for op in order_products:
                basket_items.append(create_product_data(op.product, op.count, op.price))
            return basket_items
        except Order.DoesNotExist:
            return []
    else:
        # Для анонимных пользователей используем сессию
        basket = request.session.get('basket', [])
        basket_items = []

        for item in basket:
            try:
                product = Product.objects.prefetch_related(
                    'images', 'tags', 'category'
                ).get(id=item['id'])
                basket_items.append(create_product_data(product, item['count']))
            except Product.DoesNotExist:
                continue

        return basket_items


# ========== VIEW FUNCTIONS ==========
def create_order_from_cart(request):
    """Отображение страницы оформления заказа при GET-запросе"""

    # Проверяем авторизацию
    if not request.user.is_authenticated:
        return redirect('/sign-in/')

    # Проверяем, есть ли товары в корзине
    if check_basket_empty(request.user):
        return redirect('/cart/')

    # Показываем форму оформления заказа
    return render(request, 'frontend/order.html')


def create_order_and_redirect(request):
    """Создать заказ из корзины и перенаправить на страницу заказа"""
    if not request.user.is_authenticated:
        return redirect('/sign-in/')

    order = create_order_from_basket(request.user)

    if order:
        return redirect(f'/orders/{order.id}/')
    else:
        return redirect('/cart/')


def redirect_to_latest_order(request):
    """Перенаправление на последний заказ пользователя"""
    if request.user.is_authenticated:
        latest_order = Order.objects.filter(user=request.user).order_by('-createdAt').first()
        if latest_order:
            try:
                order_id = int(latest_order.id)
                return redirect(f'/orders/{order_id}/')
            except (ValueError, TypeError):
                pass

    return redirect('/cart/')


def order_page_view(request):
    """Страница оформления нового заказа"""
    if not request.user.is_authenticated:
        return redirect('/sign-in/')

    # Проверяем корзину
    if check_basket_empty(request.user):
        return redirect('/cart/')

    return render(request, 'frontend/order.html')


def order_detail_page(request, id):
    """Страница существующего заказа"""
    if request.method == 'POST':
        from django.http import JsonResponse
        return JsonResponse({"error": "Use /api/orders/{id}/ for API requests"}, status=405)

    if not request.user.is_authenticated:
        return redirect('/sign-in/')

    try:
        order = Order.objects.get(id=id, user=request.user)
        return render(request, 'frontend/oneorder.html')
    except Order.DoesNotExist:
        return redirect('/cart/')


# ========== API VIEWS ==========
class ActiveOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /orders/ - Список заказов пользователя"""
        orders = Order.objects.filter(user=request.user).exclude(status='accepted').order_by('-createdAt')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, order=None):
        """POST /orders/ - Создание заказа из корзины"""
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        order = create_order_from_basket(request.user)

        if order:
            return Response({"orderId": order.id}, status=status.HTTP_201_CREATED)
        elif order is None:
            return Response({"error": "No basket found"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Basket is empty"}, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    """Работа с конкретным заказом"""
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        """GET: Получение данных заказа для отображения"""

        try:
            id = int(id)
        except (ValueError, TypeError):
            return Response({"error": "Invalid order ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем заказ
        order = get_object_or_404(Order, id=id)

        # Проверяем доступ
        if not check_order_access(request, order):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        # Получаем данные товаров
        products_data = self._get_products_data(order)

        # Подготавливаем данные для фронтенда
        response_data = {
            "id": order.id,
            "orderId": order.id,
            "createdAt": order.createdAt,
            "fullName": order.fullName,
            "email": order.email,
            "phone": order.phone,
            "deliveryType": order.get_deliveryType_display(),
            "paymentType": order.get_paymentType_display(),
            "city": order.city,
            "address": order.address,
            "status": order.get_status_display(),
            "totalCost": float(order.totalCost),
            "products": products_data,
            "comment": order.comment or ""
        }

        return Response(response_data)

    def post(self, request, id):
        """POST: Подтверждение заказа (отправка данных формы)"""

        try:
            id = int(id)
        except (ValueError, TypeError):
            return Response({"error": "Invalid order ID"}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=id)

        # Проверяем доступ
        if not check_order_access(request, order):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data

        # Получаем данные из Vue объекта
        full_name = data.get('fullName')
        email = data.get('email')
        phone = data.get('phone')
        city = data.get('city')
        address = data.get('address')
        delivery_type = data.get('deliveryType')
        payment_type = data.get('paymentType')

        # Обновляем поля заказа
        if full_name is not None:
            order.fullName = full_name

        if email is not None:
            order.email = email

        if phone is not None:
            order.phone = phone

        if city is not None:
            order.city = city

        if address is not None:
            order.address = address

        if delivery_type is None or delivery_type == '':
            if 'delivery' in data:
                delivery_type = data.get('delivery')
            elif order.deliveryType:
                delivery_type = order.deliveryType
            else:
                delivery_type = 'ordinary'

        # Обрабатываем значение delivery_type
        if delivery_type:
            if delivery_type == 'free':
                delivery_type = 'ordinary'

            if delivery_type in ['ordinary', 'express']:
                order.deliveryType = delivery_type
            else:
                order.deliveryType = 'ordinary'

        if payment_type is None or payment_type == '':
            if 'pay' in data:
                payment_type = data.get('pay')
            elif order.paymentType:
                payment_type = order.paymentType
            else:
                payment_type = 'online'

        # Обрабатываем значение payment_type
        if payment_type:
            if payment_type == 'random':
                payment_type = 'someone'

            if payment_type in ['online', 'someone']:
                order.paymentType = payment_type
            else:
                order.paymentType = 'online'

        # Пересчитываем стоимость
        order_products = order.products.all()
        total_product_cost = sum(float(item.price) * item.count for item in order_products)

        # Рассчитываем доставку
        delivery_price = calculate_delivery_price(order.deliveryType, total_product_cost)
        order.totalCost = total_product_cost + delivery_price

        # Устанавливаем статус
        order.status = 'confirmed'
        order.save()

        return Response({
            "orderId": order.id
        })

    def _get_products_data(self, order):
        """Получить данные товаров заказа"""

        order_products = order.products.all()

        products_data = []

        for op in order_products:
            product = op.product
            product_data = {
                'id': product.id,
                'title': product.title,
                'description': product.description,
                'price': float(op.price),
                'count': op.count,
                'date': product.created_at.strftime("%a %b %d %Y %H:%M:%S GMT%z"),
                'images': [
                    {
                        'src': image.src.url if image.src else '/static/frontend/assets/img/product.png',
                        'alt': image.alt or product.title
                    }
                    for image in product.images.all()[:1]
                ],
                'shortDescription': product.description[:100] + '...' if product.description else ''
            }
            products_data.append(product_data)

        return products_data


class OrderDetailUndefinedView(APIView):
    """Обработка запроса к заказу с undefined ID"""

    def get(self, request):
        return Response({
            "error": "Invalid order ID",
            "message": "Order ID cannot be undefined"
        }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        return Response({
            "error": "Invalid order ID",
            "message": "Order ID cannot be undefined"
        }, status=status.HTTP_400_BAD_REQUEST)


class BasketView(APIView):
    """Работа с корзиной"""

    def get(self, request):
        return Response(get_basket_items_for_user(request))

    def post(self, request):
        product_id = request.data.get('id')
        count = int(request.data.get('count', 1))
        product = get_object_or_404(
            Product.objects.prefetch_related('images', 'tags', 'category'),
            id=product_id
        )

        if request.user.is_authenticated:
            basket_order, created = Order.objects.get_or_create(
                user=request.user,
                status='accepted'
            )

            order_product, created = OrderProduct.objects.get_or_create(
                order=basket_order,
                product=product,
                defaults={'count': count, 'price': product.price}
            )

            if not created:
                order_product.count += count
                order_product.save()
            else:
                order_product.price = product.price
                order_product.save()

            return Response(get_basket_items_for_user(request))
        else:
            basket = request.session.get('basket', [])
            item_exists = False

            for item in basket:
                if item['id'] == product_id:
                    item['count'] += count
                    item_exists = True
                    break

            if not item_exists:
                basket.append({'id': product_id, 'count': count})

            request.session['basket'] = basket
            return Response(get_basket_items_for_user(request))

    def delete(self, request):
        """
        Удаление товара из корзины
        Обрабатывает строку JSON от фронтенда
        """

        if request.content_type == 'text/plain;charset=UTF-8' and request.body:
            try:
                body_str = request.body.decode('utf-8')
                data = json.loads(body_str)
                product_id = data.get('id')
                count = int(data.get('count', 1))
            except json.JSONDecodeError as e:
                return Response(
                    {"error": "Invalid JSON format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                print(f"Error: {e}")
                return Response(
                    {"error": "Error processing request"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            product_id = request.data.get('id')
            count = int(request.data.get('count', 1))

        if request.user.is_authenticated:
            try:
                basket_order = Order.objects.get(user=request.user, status='accepted')
                order_product = OrderProduct.objects.get(order=basket_order, product_id=product_id)

                if order_product.count > count:
                    order_product.count -= count
                    order_product.save()
                else:
                    order_product.delete()

                return Response(get_basket_items_for_user(request))
            except (Order.DoesNotExist, OrderProduct.DoesNotExist):
                return Response([])
        else:
            basket = request.session.get('basket', [])
            new_basket = []

            for item in basket:
                if item['id'] == product_id:
                    if item['count'] > count:
                        item['count'] -= count
                        new_basket.append(item)
                else:
                    new_basket.append(item)

            request.session['basket'] = new_basket
            return Response(get_basket_items_for_user(request))


class PaymentView(APIView):
    """Обработка оплаты"""
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            id = int(id)
        except (ValueError, TypeError):
            return Response({"error": "Invalid order ID"}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=id)

        # Проверяем, что пользователь имеет доступ к заказу
        if not check_order_access(request, order):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        # Получаем данные для оплаты
        payment_data = request.data

        # Проверяем номер карты/счета
        number = payment_data.get('number', '')
        name = payment_data.get('name', '')
        month = payment_data.get('month', '')
        year = payment_data.get('year', '')
        code = payment_data.get('code', '')

        # Создаем запись о платеже
        payment_obj = Payment.objects.create(
            order=order,
            number=number,
            name=name,
            month=month,
            year=year,
            code=code
        )

        try:
            if number:
                # Проверяем, что номер четный и не заканчивается на 0
                number_int = int(number.replace(' ', ''))
                if number_int % 2 != 0 or number_int % 10 == 0:
                    # Случайная ошибка оплаты
                    import random
                    errors = [
                        "Card number validation failed",
                        "Payment declined by bank",
                        "Insufficient funds",
                        "Card expired"
                    ]
                    error_message = random.choice(errors)
                    order.status = 'cancelled'
                    order.save()
                    payment_obj.status = 'failed'
                    payment_obj.save()
                    return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

            # Успешная оплата
            order.status = 'paid'
            order.save()
            payment_obj.status = 'completed'
            payment_obj.save()
            return Response({"result": "Payment successful"})

        except (ValueError, AttributeError):
            payment_obj.status = 'failed'
            payment_obj.save()
            return Response({"error": "Invalid number format"}, status=status.HTTP_400_BAD_REQUEST)


class PaymentStatusView(APIView):
    """Получение статуса оплаты заказа"""
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            id = int(id)
        except (ValueError, TypeError):
            return Response({"error": "Invalid order ID"}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=id)

        # Проверяем, что пользователь имеет доступ к заказу
        if not check_order_access(request, order):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            "status": order.status,
            "error": None
        })