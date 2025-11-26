"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),  # подключаем админку

    path('api/', include('shop.urls')),  # подключаем shop urls (для работы с товарами)
    path('api/', include('users.urls')),  # подключаем users urls (для работы с пользователями)
    path('api/', include('orders.urls')),  # добавляем заказы и корзину (для работы с заказами)

    path('', include('frontend.urls')),  # подключаем фронтенд
]

# Обслуживание медиа-файлов в разработке
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
