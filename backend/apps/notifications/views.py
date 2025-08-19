from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from apps.accounts.views import AdminOnlyPermission
from .utils import send_low_stock_alert
from apps.products.models import Product

@api_view(['POST'])
@permission_classes([AdminOnlyPermission])
def send_stock_alert(request, product_id):
    """Manually send low stock alert for a product"""
    try:
        product = Product.objects.get(id=product_id)
        send_low_stock_alert(product)
        return Response({'message': 'Stock alert sent successfully'})
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AdminOnlyPermission])
def notification_settings(request):
    """Get notification settings (placeholder for future expansion)"""
    return Response({
        'email_notifications': True,
        'sms_notifications': False,
        'low_stock_alerts': True,
        'new_order_alerts': True,
    })