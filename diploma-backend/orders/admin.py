from django.contrib import admin
from .models import Order, OrderProduct, Cart, Payment


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Order admin configuration."""

    list_display = ('id', 'user', 'fullName', 'email', 'phone', 'createdAt', 'deliveryType', 'paymentType', 'totalCost', 'status')
    list_filter = ('deliveryType', 'paymentType', 'status', 'createdAt')
    search_fields = ('fullName', 'email', 'phone', 'user__username')
    inlines = [OrderProductInline]


@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    """Order product admin configuration."""

    list_display = ('id', 'order', 'product', 'count', 'price')
    search_fields = ('product__title',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Cart admin configuration."""

    list_display = ('id', 'user', 'product', 'count', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'product__title')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment admin configuration."""

    list_display = ('id', 'order', 'number', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__id', 'number')
