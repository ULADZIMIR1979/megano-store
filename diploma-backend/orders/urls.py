from django.urls import path
from . import views

urlpatterns = [
    # ========== API ЗАКАЗОВ (как в swagger) ==========

    # GET: список заказов, POST: создание заказа
    path('orders/', views.ActiveOrderView.as_view(), name='api_orders'),
    path('orders', views.ActiveOrderView.as_view(), name='api_orders_no_slash'),

    # GET: данные заказа, POST: подтверждение заказа
    path('orders/<int:id>/', views.OrderDetailView.as_view(), name='api_order_detail'),
    path('orders/<int:id>', views.OrderDetailView.as_view(), name='api_order_detail_no_slash'),

    # GET: данные заказа, POST: подтверждение заказа (совместимость с фронтендом)
    path('order/<int:id>/', views.OrderDetailView.as_view(), name='api_order_legacy'),
    path('order/<int:id>', views.OrderDetailView.as_view(), name='api_order_legacy_no_slash'),

    # ========== HTML СТРАНИЦЫ (для фронтенда) ==========

    # Страница оформления заказа
    path('order/', views.order_page_view, name='order_page'),  # НОВЫЙ МАРШРУТ!

    # Страница существующего заказа
    path('order-page/<int:id>/', views.order_detail_page, name='order_page_detail'),
    path('order-page/<int:id>', views.order_detail_page, name='order_page_detail_no_slash'),

    # ========== КОРЗИНА API ==========

    # GET: получить корзину, POST: добавить, DELETE: удалить
    path('basket/', views.BasketView.as_view(), name='basket_api'),
    path('basket', views.BasketView.as_view(), name='basket_api_no_slash'),

    # ========== ОПЛАТА API ==========

    # POST: оплата заказа
    path('payment/<int:id>/', views.PaymentView.as_view(), name='payment_api'),
    path('payment/<int:id>', views.PaymentView.as_view(), name='payment_api_no_slash'),

    # GET: статус оплаты
    path('payment-status/<int:id>/', views.PaymentStatusView.as_view(), name='payment_status_api'),
    path('payment-status/<int:id>', views.PaymentStatusView.as_view(), name='payment_status_api_no_slash'),

]