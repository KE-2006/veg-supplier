from rest_framework import serializers
from .models import Product, Category, StockMovement

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = '__all__'
    
    def get_product_count(self, obj):
        return obj.products.filter(availability_status='available').count()

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value
    
    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative")
        return value

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products with stock tracking"""
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def update(self, instance, validated_data):
        # Track stock changes
        old_stock = instance.stock_quantity
        new_stock = validated_data.get('stock_quantity', old_stock)
        
        if old_stock != new_stock:
            # Create stock movement record
            StockMovement.objects.create(
                product=instance,
                movement_type='adjustment',
                quantity=new_stock - old_stock,
                previous_stock=old_stock,
                new_stock=new_stock,
                reason='Admin stock adjustment',
                created_by=self.context['request'].user
            )
        
        return super().update(instance, validated_data)

class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for stock movements"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = '__all__'
