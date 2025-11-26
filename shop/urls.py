from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.categories_list, name='categories'), # добавляем категории

    path('catalog/', views.catalog, name='catalog'), # добавляем каталог

    path('products/popular/', views.popular_products, name='popular_products'), # добавляем популярные товары
    path('products/limited/', views.limited_products, name='limited_products'), # добавляем товары со скидкой
    path('product/<int:id>/', views.product_detail, name='product_detail'), # добавляем товары

    path('banners/', views.banners, name='banners'),  # добавляем баннеры

    path('sales/', views.sales, name='sales'),  # добавляем распродажи

    path('tags/', views.tags_list, name='tags'),  # добавляем теги
]
