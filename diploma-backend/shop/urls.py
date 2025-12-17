from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # Каталог и товары
    path('catalog/', views.ProductListView.as_view(), name='product-list'),
    path('catalog', views.ProductListView.as_view(), name='product-list_no_slash'),
    path('product/<int:id>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('product/<int:id>', views.ProductDetailView.as_view(), name='product-detail_no_slash'),
    path('products/popular/', views.ProductPopularView.as_view(), name='product-popular'),
    path('products/popular', views.ProductPopularView.as_view(), name='product-popular_no_slash'),
    path('products/limited/', views.ProductLimitedView.as_view(), name='product-limited'),
    path('products/limited', views.ProductLimitedView.as_view(), name='product-limited_no_slash'),
    path('product/<int:id>/review/', views.ProductReviewView.as_view(), name='product-review'),
    path('product/<int:id>/review', views.ProductReviewView.as_view(), name='product-review_no_slash'),

    # Заказы теперь обрабатываются в orders/urls.py

    # Скидки и категории
    path('sales/', views.SaleListView.as_view(), name='sale-list'),
    path('sales', views.SaleListView.as_view(), name='sale-list_no_slash'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories', views.CategoryListView.as_view(), name='category-list_no_slash'),
    path('tags/', views.TagListView.as_view(), name='tag-list'),
    path('tags', views.TagListView.as_view(), name='tag-list_no_slash'),
    path('banners/', views.BannerListView.as_view(), name='banner-list'),
    path('banners', views.BannerListView.as_view(), name='banner-list_no_slash'),


]
