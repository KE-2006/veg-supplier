from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    """Extended user model for both admin and customer accounts"""
    USER_TYPES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='customer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    is_active_customer = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.user_type})"

class CustomerProfile(models.Model):
    """Additional customer-specific information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    preferred_delivery_time = models.CharField(max_length=20, blank=True, null=True)
    loyalty_points = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"Profile for {self.user.username}"
