from rest_framework import serializers
from .models import Order, OrderItem, Invoice, Cart, CartItem
from apps.products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_unit = serializers.CharField(source='product.unit', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ('total_price',)

class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders"""
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('order_number', 'subtotal', 'tax', 'total')

class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders"""
    items = serializers.ListField(write_only=True)
    
    class Meta:
        model = Order
        fields = ('delivery_date', 'delivery_address', 'notes', 'items')
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(
            customer=self.context['request'].user,
            **validated_data
        )
        
        # Create order items and update stock
        for item_data in items_data:
            product_id = item_data['product_id']
            quantity = item_data['quantity']
            
            try:
                from apps.products.models import Product, StockMovement
                product = Product.objects.get(id=product_id)
                
                # Check stock availability
                if product.stock_quantity < quantity:
                    raise serializers.ValidationError(
                        f"Not enough stock for {product.name}. Available: {product.stock_quantity}"
                    )
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price_per_unit=product.price
                )
                
                # Update stock
                old_stock = product.stock_quantity
                product.stock_quantity -= quantity
                product.save()
                
                # Track stock movement
                StockMovement.objects.create(
                    product=product,
                    movement_type='out',
                    quantity=-quantity,
                    previous_stock=old_stock,
                    new_stock=product.stock_quantity,
                    reason=f'Order {order.order_number}',
                    created_by=None
                )
                
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product with id {product_id} not found")
        
        return order

class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for invoices"""
    order_details = OrderSerializer(source='order', read_only=True)
    
    class Meta:
        model = Invoice
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items"""
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = '__all__'
        read_only_fields = ('cart',)

class CartSerializer(serializers.ModelSerializer):
    """Serializer for shopping cart"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = '__all__'