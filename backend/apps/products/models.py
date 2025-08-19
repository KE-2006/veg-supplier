from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from PIL import Image

class Category(models.Model):
    """Product categories like vegetables, fruits, boxes"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """Main product model"""
    AVAILABILITY_CHOICES = (
        ('available', 'Available'),
        ('out_of_stock', 'Out of Stock'),
        ('discontinued', 'Discontinued'),
    )
    
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    stock_quantity = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=50, default='kg')  # kg, pieces, boxes, etc.
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available')
    low_stock_threshold = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - ${self.price}/{self.unit}"
    
    @property
    def is_low_stock(self):
        """Check if product is low on stock"""
        return self.stock_quantity <= self.low_stock_threshold
    
    @property
    def is_available(self):
        """Check if product is available for purchase"""
        return self.availability_status == 'available' and self.stock_quantity > 0
    
    def save(self, *args, **kwargs):
        # Update availability based on stock
        if self.stock_quantity == 0 and self.availability_status == 'available':
            self.availability_status = 'out_of_stock'
        elif self.stock_quantity > 0 and self.availability_status == 'out_of_stock':
            self.availability_status = 'available'
        
        super().save(*args, **kwargs)
        
        # Resize image if it exists
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                output_size = (800, 800)
                img.thumbnail(output_size)
                img.save(self.image.path)

class StockMovement(models.Model):
    """Track stock changes for inventory management"""
    MOVEMENT_TYPES = (
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    previous_stock = models.PositiveIntegerField()
    new_stock = models.PositiveIntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.movement_type} - {self.quantity}"
