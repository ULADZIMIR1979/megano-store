from rest_framework import serializers
from .models import Category, Product, ProductImage, Review, Tag, Specification


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'subcategories']

    def get_subcategories(self, obj):
        subcategories = Category.objects.filter(parent=obj)
        return CategorySerializer(subcategories, many=True).data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['src', 'alt']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['author', 'email', 'text', 'rate', 'date']


# Сериализатор для списка товаров (каталог)
class ProductShortSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    rating = serializers.FloatField()
    price = serializers.FloatField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'title', 'description', 'price', 'count',
            'freeDelivery', 'images', 'tags', 'reviews', 'rating', 'limited'
        ]

    def get_images(self, obj):
        images = obj.images.all()
        if images.exists():
            # Если есть реальные изображения
            return [{
                'src': image.src.url if image.src else '/static/frontend/assets/img/product.png',
                'alt': image.alt or obj.title
            } for image in images]
        else:
            # Заглушка если изображений нет
            return [{
                'src': '/static/frontend/assets/img/product.png',
                'alt': obj.title
            }]

    def get_reviews(self, obj):
        return obj.reviews.count()


# Сериализатор для детальной страницы товара
class ProductFullSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    reviews = ReviewSerializer(many=True, read_only=True)
    specifications = serializers.SerializerMethodField()
    rating = serializers.FloatField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'title', 'description', 'fullDescription',
            'price', 'count', 'freeDelivery', 'images', 'tags', 'reviews',
            'specifications', 'rating', 'limited'
        ]

    def get_images(self, obj):
        images = obj.images.all()
        return [{'src': image.src.url, 'alt': image.alt} for image in images]

    def get_tags(self, obj):
        tags = obj.tags.all()
        return [{'id': tag.id, 'name': tag.name} for tag in tags]

    def get_specifications(self, obj):
        specs = obj.specifications.all()
        return [{'name': spec.name, 'value': spec.value} for spec in specs]