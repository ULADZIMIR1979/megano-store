from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='frontend/index.html'), name='home'),
    path('catalog', TemplateView.as_view(template_name='frontend/catalog.html'), name='catalog'),
    path('catalog/', TemplateView.as_view(template_name='frontend/catalog.html'), name='catalog_slash'),
    path('sale', TemplateView.as_view(template_name='frontend/sale.html'), name='sale'),
    path('sale/', TemplateView.as_view(template_name='frontend/sale.html'), name='sale_slash'),
    path('cart', TemplateView.as_view(template_name='frontend/cart.html'), name='cart'),
    path('cart/', TemplateView.as_view(template_name='frontend/cart.html'), name='cart_slash'),
    path('profile', TemplateView.as_view(template_name='frontend/profile.html'), name='profile'),
    path('profile/', TemplateView.as_view(template_name='frontend/profile.html'), name='profile_slash'),
    path('sign-in', TemplateView.as_view(template_name='frontend/signIn.html'), name='sign_in'),
    path('sign-in/', TemplateView.as_view(template_name='frontend/signIn.html'), name='sign_in_slash'),
    path('sign-up', TemplateView.as_view(template_name='frontend/signUp.html'), name='sign_up'),
    path('sign-up/', TemplateView.as_view(template_name='frontend/signUp.html'), name='sign_up_slash'),
]