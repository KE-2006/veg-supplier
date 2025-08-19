from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('', views.ProductListCreateView.as_view(), name='product-list'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('low-stock/', views.low_stock_products, name='low-stock'),
    path('stock-movements/', views.stock_movements, name='stock-movements'),
    path('analytics/', views.product_analytics, name='product-analytics'),
]
