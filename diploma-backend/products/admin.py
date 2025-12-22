from django.contrib import admin
from .models import Category, Tag, Product, ProductImage, Review, Specification, Sale


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class SpecificationInline(admin.TabularInline):
    model = Specification
    extra = 1


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'parent')
    list_filter = ('parent',)
    search_fields = ('title',)
    prepopulated_fields = {'title': ('title',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'price', 'count', 'available', 'limited', 'freeDelivery', 'rating')
    list_filter = ('category', 'available', 'limited', 'freeDelivery', 'created_at', 'tags')
    search_fields = ('title', 'description')
    prepopulated_fields = {'title': ('title',)}

    filter_horizontal = ('tags',)

    inlines = [ProductImageInline, SpecificationInline, ReviewInline]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'price', 'salePrice', 'dateFrom', 'dateTo', 'title')
    list_filter = ('dateFrom', 'dateTo')
    search_fields = ('title', 'product__title')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'alt')
    search_fields = ('product__title', 'alt')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'author', 'email', 'rate', 'date')
    list_filter = ('rate', 'date')
    search_fields = ('product__title', 'author', 'email')


@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'name', 'value')
    search_fields = ('product__title', 'name', 'value')
