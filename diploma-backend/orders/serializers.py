from rest_framework import serializers
from .models import Order, OrderProduct, Cart, Payment
from shop.models import Product
from shop.serializers import ProductShortSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class OrderProductSerializer(serializers.ModelSerializer):
    """Сериализатор для товаров в заказе"""

    date = serializers.SerializerMethodField(read_only=True)
    id = serializers.IntegerField(source='product.id', read_only=True)
    category = serializers.IntegerField(source='product.category.id', read_only=True)
    title = serializers.CharField(source='product.title', read_only=True)
    description = serializers.CharField(source='product.description', read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    count = serializers.IntegerField()
    freeDelivery = serializers.BooleanField(source='product.freeDelivery', read_only=True)
    images = serializers.SerializerMethodField(read_only=True)
    tags = serializers.SerializerMethodField(read_only=True)
    reviews = serializers.SerializerMethodField(read_only=True)
    rating = serializers.FloatField(source='product.rating', read_only=True)
    limited = serializers.BooleanField(source='product.limited', read_only=True)
    available = serializers.BooleanField(source='product.available', read_only=True)
    salePrice = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderProduct
        fields = [
            'id', 'category', 'title', 'description', 'price', 'count', 'date',
            'freeDelivery', 'images', 'tags', 'reviews', 'rating', 'limited',
            'available', 'salePrice'
        ]

    def get_date(self, obj):
        """Форматирование даты как в swagger"""
        return obj.product.created_at.strftime("%a %b %d %Y %H:%M:%S GMT%z")

    def get_images(self, obj):
        serializer = ProductShortSerializer(obj.product, context=self.context)
        return serializer.data.get('images', [])

    def get_tags(self, obj):
        serializer = ProductShortSerializer(obj.product, context=self.context)
        return serializer.data.get('tags', [])

    def get_reviews(self, obj):
        serializer = ProductShortSerializer(obj.product, context=self.context)
        return serializer.data.get('reviews', 0)

    def get_salePrice(self, obj):
        serializer = ProductShortSerializer(obj.product, context=self.context)
        return serializer.data.get('salePrice', None)


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказа"""

    products = OrderProductSerializer(source='products', many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'createdAt', 'fullName', 'email', 'phone',
            'deliveryType', 'city', 'address', 'paymentType',
            'status', 'totalCost', 'products', 'comment'
        ]


class BasketItemSerializer(serializers.Serializer):
    """Сериализатор для элементов корзины (работа с сессией)"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    price = serializers.FloatField()
    count = serializers.IntegerField()
    images = serializers.ListField(child=serializers.DictField())


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'number', 'name', 'month', 'year', 'code', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

    def validate_number(self, value):
        if len(value) > 8:
            raise serializers.ValidationError("Номер не должен быть длиннее 8 цифр")
        if not value.isdigit():
            raise serializers.ValidationError("Номер должен содержать только цифры")
        if int(value) % 2 != 0:
            raise serializers.ValidationError("Номер должен быть четным")
        return value


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'product', 'count', 'added_at']
        read_only_fields = ['id', 'added_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        product_data = ProductShortSerializer(instance.product, context=self.context).data
        representation['product'] = product_data
        return representation


class BasketSerializer(serializers.Serializer):
    """Сериализатор для корзины"""
    items = BasketItemSerializer(many=True)