from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Order, OrderItem, Invoice, Cart, CartItem
from .serializers import (OrderSerializer, OrderCreateSerializer, InvoiceSerializer,
                         CartSerializer, CartItemSerializer)
from apps.accounts.views import AdminOnlyPermission
from apps.notifications.utils import send_order_notification

class OrderListCreateView(generics.ListCreateAPIView):
    """List orders or create new order"""
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return Order.objects.select_related('customer').prefetch_related('items').all()
        else:
            return Order.objects.filter(customer=user).prefetch_related('items')
    
    def perform_create(self, serializer):
        order = serializer.save()
        
        # Clear customer's cart after successful order
        try:
            cart = Cart.objects.get(customer=self.request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass
        
        # Send notifications
        send_order_notification(order, 'new_order')

class OrderDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update order"""
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return Order.objects.all()
        else:
            return Order.objects.filter(customer=user)
    
    def perform_update(self, serializer):
        order = serializer.save()
        
        # Send notification if status changed
        if 'status' in serializer.validated_data:
            send_order_notification(order, 'status_update')

@api_view(['GET'])
@permission_classes([AdminOnlyPermission])
def order_analytics(request):
    """Get order analytics for admin dashboard"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Daily sales
    daily_sales = Order.objects.filter(
        created_at__date=today,
        status__in=['completed', 'in_process']
    ).aggregate(
        total_revenue=Sum('total'),
        total_orders=Count('id')
    )
    
    # Weekly sales
    weekly_sales = Order.objects.filter(
        created_at__date__gte=week_ago,
        status__in=['completed', 'in_process']
    ).aggregate(
        total_revenue=Sum('total'),
        total_orders=Count('id')
    )
    
    # Monthly sales
    monthly_sales = Order.objects.filter(
        created_at__date__gte=month_ago,
        status__in=['completed', 'in_process']
    ).aggregate(
        total_revenue=Sum('total'),
        total_orders=Count('id')
    )
    
    # New vs returning customers this month
    from apps.accounts.models import User
    new_customers = User.objects.filter(
        user_type='customer',
        date_joined__date__gte=month_ago
    ).count()
    
    # Order status distribution
    status_distribution = Order.objects.values('status').annotate(
        count=Count('id')
    )
    
    return Response({
        'daily_sales': daily_sales,
        'weekly_sales': weekly_sales,
        'monthly_sales': monthly_sales,
        'new_customers_this_month': new_customers,
        'status_distribution': list(status_distribution),
    })

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def cart_view(request):
    """Get or create customer cart"""
    if request.user.user_type != 'customer':
        return Response({'error': 'Only customers can access cart'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    cart, created = Cart.objects.get_or_create(customer=request.user)
    
    if request.method == 'GET':
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Add item to cart
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        try:
            from apps.products.models import Product
            product = Product.objects.get(id=product_id)
            
            if not product.is_available:
                return Response({'error': 'Product not available'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            if product.stock_quantity < quantity:
                return Response({'error': f'Not enough stock. Available: {product.stock_quantity}'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            serializer = CartSerializer(cart)
            return Response(serializer.data)
            
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, 
                           status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def cart_item_view(request, item_id):
    """Update or remove cart item"""
    if request.user.user_type != 'customer':
        return Response({'error': 'Only customers can modify cart'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        cart = Cart.objects.get(customer=request.user)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        
        if request.method == 'PUT':
            quantity = request.data.get('quantity', 1)
            
            if cart_item.product.stock_quantity < quantity:
                return Response({'error': f'Not enough stock. Available: {cart_item.product.stock_quantity}'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            cart_item.quantity = quantity
            cart_item.save()
            
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        
        elif request.method == 'DELETE':
            cart_item.delete()
            serializer = CartSerializer(cart)
            return Response(serializer.data)
            
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        return Response({'error': 'Cart item not found'}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_invoice(request, order_id):
    """Generate PDF invoice for order"""
    try:
        if request.user.user_type == 'admin':
            order = Order.objects.get(id=order_id)
        else:
            order = Order.objects.get(id=order_id, customer=request.user)
        
        # Create or get invoice
        invoice, created = Invoice.objects.get_or_create(order=order)
        
        # Generate PDF
        from .utils import generate_invoice_pdf
        pdf_path = generate_invoice_pdf(invoice)
        invoice.pdf_file = pdf_path
        invoice.save()
        
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)
        
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, 
                       status=status.HTTP_404_NOT_FOUND)