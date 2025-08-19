from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

class Order(models.Model):
    """Customer orders"""
    STATUS_CHOICES = (
        ('new', 'New'),
        ('in_process', 'In Process'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    customer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    delivery_date = models.DateField()
    delivery_address = models.TextField()
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_number} - {self.customer.username}"
    
    def calculate_totals(self):
        """Calculate order totals"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.tax = self.subtotal * Decimal('0.10')  # 10% tax
        self.total = self.subtotal + self.tax
        self.save()
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            import random
            import string
            self.order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    """Items within an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price_per_unit = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price_per_unit
        super().save(*args, **kwargs)
        # Update order totals
        self.order.calculate_totals()
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class Invoice(models.Model):
    """Invoice for orders"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True)
    issue_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateField()
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} for Order {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate unique invoice number
            import random
            import string
            self.invoice_number = 'INV-' + ''.join(random.choices(string.digits, k=6))
        
        if not self.due_date:
            self.due_date = (self.issue_date + timezone.timedelta(days=30)).date()
        
        super().save(*args, **kwargs)

class Cart(models.Model):
    """Shopping cart for customers"""
    customer = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.customer.username}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    """Items in shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('cart', 'product')
    
    @property
    def total_price(self):
        return self.quantity * self.product.price
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity} in {self.cart.customer.username}'s cart"
