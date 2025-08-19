from django.urls import path
from . import views

urlpatterns = [
    path('stock-alert/<int:product_id>/', views.send_stock_alert, name='send-stock-alert'),
    path('settings/', views.notification_settings, name='notification-settings'),
]