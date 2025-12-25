from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from orders.views import create_order_from_cart, order_detail_page
from products.views import order_page, ProductDetailView, product_page
from .views import get_csrf_token
from django.urls import path
from .views import DebugSignInView


schema_view = get_schema_view(
    openapi.Info(
        title="MegaNo API",
        default_version='v1',
        description="API documentation for MegaNo e-commerce platform",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include('users.urls')),
    path('api/', include('products.urls')),
    path('api/', include('orders.urls')),
    path('api/debug-sign-in/', DebugSignInView.as_view(), name='debug_sign_in'),

    path('api/csrf/', get_csrf_token, name='csrf'),

    # 2. Frontend маршруты (рендеринг страниц)
    path('orders/create/', create_order_from_cart, name='create_order'),  # Создание заказа через GET
    path('orders/detail/<int:id>/', order_detail_page, name='order_detail'),  # Просмотр заказа

    # 3. Статические страницы фронтенда
    path("", include("frontend.urls")),  # Шаблоны для Vue.js
    
    # 4. Маршруты для прямого доступа к продуктам (без /api/)
    path('product/<int:id>/', product_page, name='product-page'),  # Отображение HTML-страницы продукта
    path('product/<int:id>', product_page, name='product-page_no_slash'),   # Без слэша в конце

    # 5. Документация
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
