from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from orders.models import Order, OrderProduct, Payment
from products.models import Product, Category, ProductImage
from decimal import Decimal

User = get_user_model()


class OrderModelTest(TestCase):
    def setUp(self):
        # Создаем тестового пользователя с обязательным username
        self.user = User.objects.create_user(
            username='testuser',  # ДОБАВЬТЕ ЭТУ СТРОКУ
            email='test@example.com',
            password='testpass123',
        )

        # Создаем категорию и продукт для тестирования
        self.category = Category.objects.create(title='Test Category')
        self.product = Product.objects.create(
            category=self.category,
            title='Test Product',
            description='Test description',
            price=Decimal('100.00'),
            count=10,
            freeDelivery=True,
            rating=4.5,
            available=True
        )

    def test_order_creation(self):
        """Тест создания заказа"""
        order = Order.objects.create(
            user=self.user,
            fullName='Test User',
            email='test@example.com',
            phone='+1234567890',
            deliveryType='ordinary',
            paymentType='online',
            totalCost=Decimal('100.00'),
            status='created',
            city='Test City',
            address='Test Address'
        )

        self.assertEqual(order.fullName, 'Test User')
        self.assertEqual(order.email, 'test@example.com')
        self.assertEqual(order.phone, '+1234567890')
        self.assertEqual(order.totalCost, Decimal('100.00'))
        self.assertEqual(order.status, 'created')
        self.assertEqual(str(order), f"Order {order.id} by Test User")

    def test_order_product_creation(self):
        """Тест создания товара в заказе"""
        order = Order.objects.create(
            user=self.user,
            fullName='Test User',
            email='test@example.com',
            phone='+1234567890',
            deliveryType='ordinary',
            paymentType='online',
            totalCost=Decimal('100.00'),
            status='created'
        )

        order_product = OrderProduct.objects.create(
            order=order,
            product=self.product,
            count=2,
            price=Decimal('100.00')
        )

        self.assertEqual(order_product.product, self.product)
        self.assertEqual(order_product.count, 2)
        self.assertEqual(order_product.price, Decimal('100.00'))
        self.assertEqual(str(order_product), f"{self.product.title} x2")

    def test_payment_creation(self):
        """Тест создания платежа"""
        order = Order.objects.create(
            user=self.user,
            fullName='Test User',
            email='test@example.com',
            phone='+1234567890',
            deliveryType='ordinary',
            paymentType='online',
            totalCost=Decimal('100.00'),
            status='created'
        )

        payment = Payment.objects.create(
            order=order,
            number='12345678',
            name='Test Card',
            month='12',
            year='2025',
            code='123'
        )

        self.assertEqual(payment.order, order)
        self.assertEqual(payment.number, '12345678')
        self.assertEqual(payment.name, 'Test Card')
        self.assertEqual(str(payment), f"Payment for order {order.id}")


class OrderAPITest(APITestCase):
    def setUp(self):
        # Создаем тестового пользователя с username
        self.user = User.objects.create_user(
            username='testuser',  # ДОБАВЬТЕ ЭТУ СТРОКУ
            email='test@example.com',
            password='testpass123',
            # Добавьте другие обязательные поля
            first_name='Test',
            last_name='User',
        )

        # Создаем категорию и продукт
        self.category = Category.objects.create(title='Test Category')
        self.product = Product.objects.create(
            category=self.category,
            title='Test Product',
            description='Test description',
            price=Decimal('100.00'),
            count=10,
            freeDelivery=True,
            rating=4.5,
            available=True
        )

        # Авторизуемся
        self.client.force_authenticate(user=self.user)

    def test_create_order(self):
        """Тест создания заказа через API"""
        # Сначала добавим товар в корзину (создадим заказ с status='accepted')
        order = Order.objects.create(
            user=self.user,
            fullName='',
            email='',
            phone='',
            deliveryType='ordinary',
            paymentType='online',
            status='accepted'  # Это статус корзины
        )

        # Добавим товар в заказ
        OrderProduct.objects.create(
            order=order,
            product=self.product,
            count=1,
            price=Decimal('100.00')
        )

        # Теперь создадим заказ из корзины
        url = reverse('api_orders')
        response = self.client.post(url)

        # Проверяем, что заказ был создан
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('orderId', response.data)

    def test_get_orders_list(self):
        """Тест получения списка заказов"""
        # Создаем несколько заказов
        order1 = Order.objects.create(
            user=self.user,
            fullName='Test User',
            email='test@example.com',
            phone='+1234567890',
            deliveryType='ordinary',
            paymentType='online',
            totalCost=Decimal('100.00'),
            status='created'
        )

        order2 = Order.objects.create(
            user=self.user,
            fullName='Test User',
            email='test@example.com',
            phone='+1234567890',
            deliveryType='express',
            paymentType='someone',
            totalCost=Decimal('20.00'),
            status='confirmed'
        )

        url = reverse('api_orders')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем количество заказов (исключая корзину)
        orders_count = Order.objects.filter(user=self.user).exclude(status='accepted').count()
        self.assertEqual(len(response.data), orders_count)

    def test_get_order_detail(self):
        """Тест получения деталей заказа"""
        # Создаем заказ
        order = Order.objects.create(
            user=self.user,
            fullName='Test User',
            email='test@example.com',
            phone='+1234567890',
            deliveryType='ordinary',
            paymentType='online',
            totalCost=Decimal('100.00'),
            status='confirmed'
        )

        # Добавляем товар в заказ
        OrderProduct.objects.create(
            order=order,
            product=self.product,
            count=1,
            price=Decimal('100.00')
        )

        url = reverse('api_order_detail', kwargs={'id': order.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], order.id)
        self.assertEqual(response.data['fullName'], 'Test User')
        # Проверяем наличие продуктов в ответе
        self.assertIn('products', response.data)

    def test_update_order(self):
        """Тест обновления заказа"""
        # Создаем заказ
        order = Order.objects.create(
            user=self.user,
            fullName='Old Name',
            email='old@example.com',
            phone='+1234567890',
            deliveryType='ordinary',
            paymentType='online',
            totalCost=Decimal('100.00'),
            status='created'
        )

        url = reverse('api_order_detail', kwargs={'id': order.id})
        data = {
            'fullName': 'New Name',
            'email': 'new@example.com',
            'phone': '+0987654321',
            'city': 'New City',
            'address': 'New Address',
            'deliveryType': 'express',
            'paymentType': 'someone'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('orderId', response.data)

        order.refresh_from_db()
        self.assertEqual(order.fullName, 'New Name')
        self.assertEqual(order.email, 'new@example.com')
        self.assertEqual(order.deliveryType, 'express')
        self.assertEqual(order.paymentType, 'someone')
        self.assertEqual(order.status, 'confirmed')


class PaymentAPITest(APITestCase):
    def setUp(self):
        # Создаем тестового пользователя с username
        self.user = User.objects.create_user(
            username='testuser',  # ДОБАВЬТЕ ЭТУ СТРОКУ
            email='test@example.com',
            password='testpass123'
        )

        # Создаем заказ
        self.order = Order.objects.create(
            user=self.user,
            fullName='Test User',
            email='test@example.com',
            phone='+1234567890',
            deliveryType='ordinary',
            paymentType='online',
            totalCost=Decimal('100.00'),
            status='confirmed'
        )

        # Авторизуемся
        self.client.force_authenticate(user=self.user)

    def test_payment_processing(self):
        """Тест обработки платежа"""
        url = reverse('payment_api', kwargs={'id': self.order.id})
        data = {
            'number': '12345678',  # Четное число, не заканчивающееся на 0
            'name': 'Test Card',
            'month': '12',
            'year': '2025',
            'code': '123'
        }

        response = self.client.post(url, data, format='json')

        # Проверяем, что платеж прошел успешно
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['result'], 'Payment successful')

        # Проверяем, что статус заказа изменился на 'paid'
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')

        # Проверяем, что создался объект Payment
        payment = Payment.objects.filter(order=self.order).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'completed')

    def test_payment_failure(self):
        """Тест отказа платежа"""
        url = reverse('payment_api', kwargs={'id': self.order.id})
        data = {
            'number': '12345679',  # Нечетное число - должно вызвать ошибку
            'name': 'Test Card',
            'month': '12',
            'year': '2025',
            'code': '123'
        }

        response = self.client.post(url, data, format='json')

        # Проверяем, что платеж отклонен
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

        # Проверяем, что статус заказа изменился на 'cancelled'
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')

        # Проверяем, что создался объект Payment со статусом 'failed'
        payment = Payment.objects.filter(order=self.order).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'failed')