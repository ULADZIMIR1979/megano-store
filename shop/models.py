from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    fullName = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'auth_user'


class Category(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               verbose_name='Родительская категория')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Изображение')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название тега')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    fullDescription = models.TextField(blank=True, verbose_name='Полное описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    count = models.IntegerField(default=0, verbose_name='Количество')
    limited = models.BooleanField(default=False, verbose_name='Ограниченный тираж')
    freeDelivery = models.BooleanField(default=False, verbose_name='Бесплатная доставка')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    rating = models.FloatField(default=0, verbose_name='Рейтинг')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='Теги')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    src = models.ImageField(upload_to='products/')
    alt = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Image for {self.product.title}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    author = models.CharField(max_length=100, verbose_name='Автор')
    email = models.EmailField(verbose_name='Email')
    text = models.TextField(verbose_name='Текст отзыва')
    rate = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='Оценка')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f"Review by {self.author} for {self.product.title}"


class Specification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    name = models.CharField(max_length=100, verbose_name='Название')
    value = models.CharField(max_length=100, verbose_name='Значение')

    class Meta:
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'

    def __str__(self):
        return f"{self.name}: {self.value}"
