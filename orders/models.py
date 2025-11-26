from django.db import models
from shop.models import Product, User

class Order(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'Принят'),
        ('paid', 'Оплачен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    DELIVERY_CHOICES = [
        ('free', 'Обычная доставка'),
        ('express', 'Экспресс доставка'),
    ]
    PAYMENT_CHOICES = [
        ('online', 'Онлайн картой'),
        ('random', 'Онлайн со случайного счёта'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    fullName = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    createdAt = models.DateTimeField(auto_now_add=True)
    deliveryType = models.CharField(max_length=10, choices=DELIVERY_CHOICES, default='free')
    paymentType = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='online')
    totalCost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='accepted')
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"Order {self.id} by {self.fullName}"

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.title} x{self.count}"
