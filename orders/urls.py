from django.urls import path
from . import views

urlpatterns = [
    path('basket/', views.basket, name='basket'),
    path('orders/', views.orders_list, name='orders_list'),
    path('orders/<int:id>/', views.order_detail, name='order_detail'),
]