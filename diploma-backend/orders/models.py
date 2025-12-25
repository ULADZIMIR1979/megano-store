from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создан'),
        ('accepted', 'Принят'),
        ('confirmed', 'Подтвержден'),
        ('paid', 'Оплачен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    DELIVERY_CHOICES = [
        ('ordinary', 'Обычная доставка'),
        ('express', 'Экспресс доставка'),
        ('free', 'Бесплатная доставка'),
    ]

    PAYMENT_CHOICES = [
        ('online', 'Онлайн картой'),
        ('someone', 'Онлайн со случайного чужого счета'),
        ('random', 'Онлайн со случайного счёта'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True)
    fullName = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    createdAt = models.DateTimeField(auto_now_add=True)
    
    deliveryType = models.CharField(
        max_length=10,
        choices=DELIVERY_CHOICES,
        default='ordinary'
    )

    paymentType = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default='online'
    )

    totalCost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='created')

    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"Order {self.id} by {self.fullName}"

    class Meta:
        indexes = [
            models.Index(fields=['createdAt']),
            models.Index(fields=['status']),
            models.Index(fields=['user']),
            models.Index(fields=['-createdAt']),  # Для сортировки по дате создания (новые первыми)
            models.Index(fields=['status', 'createdAt']),  # Комбинированный индекс для фильтрации по статусу и сортировки по дате
        ]


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    count = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.title} x{self.count}"

    class Meta:
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
            models.Index(fields=['order', 'product']),  # Комбинированный индекс для быстрого доступа к товарам в заказе
        ]


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    number = models.CharField(max_length=20, verbose_name='Номер карты/счёта')
    name = models.CharField(max_length=100, verbose_name='Имя владельца', blank=True)
    month = models.CharField(max_length=2, verbose_name='Месяц', blank=True)
    year = models.CharField(max_length=4, verbose_name='Год', blank=True)
    code = models.CharField(max_length=4, verbose_name='CVV/CVC', blank=True)
    status = models.CharField(max_length=20, verbose_name='Статус платежа', default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Payment for order {self.order.id}"


class Cart(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    count = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        app_label = 'orders'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['product']),
            models.Index(fields=['user', 'product']),  # Комбинированный индекс для быстрого доступа к товарам в корзине пользователя
        ]

    def __str__(self):
        return f"Cart item: {self.product.title} x{self.count}"
