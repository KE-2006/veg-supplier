from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('customers/', views.customer_list, name='customer-list'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer-detail'),
]
