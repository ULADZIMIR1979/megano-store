from rest_framework import serializers
from .models import Category, Product, ProductImage, Review, Tag, Specification, Sale
from django.core.files.storage import default_storage
import os


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'subcategories']

    def get_subcategories(self, obj):
        subcategories = Category.objects.filter(parent=obj).only('id', 'title', 'parent')
        return CategorySerializer(subcategories, many=True).data

    def get_image(self, obj):
        # Используем только нужное поле image, если оно есть
        image_url = obj.image.url if obj.image else None
        if image_url:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image_url)
            return image_url
        return '/static/frontend/assets/img/product.png'


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['src', 'alt']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        # Используем значение из сериализованных данных, чтобы избежать дополнительного обращения к файловой системе
        src_value = representation.get('src')
        if src_value:
            if request:
                representation['src'] = request.build_absolute_uri(src_value)
            else:
                representation['src'] = src_value
        else:
            representation['src'] = '/static/frontend/assets/img/product.png'
        return representation




class ReviewSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = Review
        fields = ['author', 'email', 'text', 'rate', 'date']


# Сериализатор для списка товаров (каталог)
class ProductShortSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    rating = serializers.FloatField()
    price = serializers.SerializerMethodField()
    salePrice = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'title', 'description', 'price', 'salePrice', 'date', 'count',
            'freeDelivery', 'images', 'tags', 'reviews', 'rating', 'limited',
            'available', 'salePrice'
        ]

    def get_reviews(self, obj):
        # Используем аннотацию из queryset для получения количества отзывов, чтобы избежать дополнительного запроса
        return getattr(obj, 'reviews_count', obj.reviews.count())

    def get_price(self, obj):
        return float(obj.price)

    def get_salePrice(self, obj):
        # Ищем скидку для этого продукта
        sale_obj = obj.sales.first()
        if sale_obj and sale_obj.salePrice:
            return float(sale_obj.salePrice)
        return None

    def get_date(self, obj):
        """Получить дату в нужном формате"""
        if hasattr(obj, 'created_at') and obj.created_at:
            return obj.created_at.strftime("%a %b %d %Y %H:%M:%S GMT%z")
        return None


# Сериализатор для детальной страницы товара
class ProductFullSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    specifications = serializers.SerializerMethodField()
    rating = serializers.FloatField()
    salePrice = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'title', 'description', 'fullDescription',
            'price', 'salePrice', 'count', 'date', 'freeDelivery', 'images', 'tags', 'reviews',
            'specifications', 'rating', 'limited', 'available'
        ]

    def get_specifications(self, obj):
        specs = obj.specifications.only('name', 'value')
        return [{'name': spec.name, 'value': spec.value} for spec in specs]

    def get_salePrice(self, obj):
        # Ищем скидку для этого продукта
        sale_obj = obj.sales.first()
        if sale_obj and sale_obj.salePrice:
            return float(sale_obj.salePrice)
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['date'] = instance.created_at.strftime("%a %b %d %Y %H:%M:%S GMT+000 (Coordinated Universal Time)")
        return data

    def get_date(self, obj):
        """Получить дату в нужном формате"""

        if hasattr(obj, 'created_at') and obj.created_at:
            return obj.created_at.strftime("%a %b %d %Y %H:%M:%S GMT%z")
        return None


class SaleSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    salePrice = serializers.SerializerMethodField()
    dateFrom = serializers.SerializerMethodField()
    dateTo = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = ['id', 'price', 'salePrice', 'dateFrom', 'dateTo', 'title', 'images']

    def get_price(self, obj):
        if obj.price:
            return float(obj.price)
        # Возвращаем цену из связанного продукта, если цена в скидке не указана
        return float(obj.product.price) if obj.product else 0

    def get_salePrice(self, obj):
        if obj.salePrice:
            return float(obj.salePrice)
        # Возвращаем цену из связанного продукта, если цена в скидке не указана
        return float(obj.product.price) if obj.product else 0

    def get_dateFrom(self, obj):
        if obj.dateFrom:
            return obj.dateFrom.strftime("%Y-%m-%d")
        return None

    def get_dateTo(self, obj):
        if obj.dateTo:
            return obj.dateTo.strftime("%Y-%m-%d")
        return None

    def get_title(self, obj):
        return obj.title

    def get_images(self, obj):
        # Возвращаем изображения как массив строк, как в спецификации swagger
        if obj.images:
            return obj.images
        else:
            product_images = obj.product.images.only('src', 'alt')
            if product_images.exists():
                image_urls = []
                request = self.context.get('request')
                for img in product_images:
                    if request:
                        image_urls.append(request.build_absolute_uri(img.src.url))
                    else:
                        image_urls.append(img.src.url)
                return image_urls
            else:
                request = self.context.get('request')
                if request:
                    return [request.build_absolute_uri('/static/frontend/assets/img/product.png')]
                else:
                    return ['/static/frontend/assets/img/product.png']
