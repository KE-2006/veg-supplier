from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.conf import settings
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_email_notification(subject, message, recipient_list, html_message=None):
    """Send email notification asynchronously"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email sent successfully to {recipient_list}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def send_order_notification(order, notification_type):
    """Send order-related notifications"""
    if notification_type == 'new_order':
        # Notify admins about new order
        from apps.accounts.models import User
        admins = User.objects.filter(user_type='admin')
        admin_emails = [admin.email for admin in admins if admin.email]
        
        if admin_emails:
            subject = f"New Order #{order.order_number}"
            message = f"""
            New order received:
            
            Order Number: {order.order_number}
            Customer: {order.customer.get_full_name()}
            Total: ${order.total}
            Delivery Date: {order.delivery_date}
            
            Please log in to the admin panel to process this order.
            """
            
            send_email_notification.delay(subject, message, admin_emails)
        
        # Notify customer about order confirmation
        if order.customer.email:
            subject = f"Order Confirmation #{order.order_number}"
            message = f"""
            Dear {order.customer.get_full_name()},
            
            Thank you for your order! Here are the details:
            
            Order Number: {order.order_number}
            Total: ${order.total}
            Delivery Date: {order.delivery_date}
            Delivery Address: {order.delivery_address}
            
            We'll send you updates as your order is processed.
            
            Best regards,
            Fresh Produce Team
            """
            
            send_email_notification.delay(subject, message, [order.customer.email])
    
    elif notification_type == 'status_update':
        # Notify customer about status changes
        if order.customer.email:
            status_messages = {
                'in_process': 'Your order is being prepared',
                'completed': 'Your order has been completed and is ready for delivery',
                'cancelled': 'Your order has been cancelled'
            }
            
            subject = f"Order Update #{order.order_number}"
            message = f"""
            Dear {order.customer.get_full_name()},
            
            Your order status has been updated:
            
            Order Number: {order.order_number}
            Status: {order.get_status_display()}
            {status_messages.get(order.status, '')}
            
            Best regards,
            Fresh Produce Team
            """
            
            send_email_notification.delay(subject, message, [order.customer.email])

def send_low_stock_alert(product):
    """Send low stock alert to admins"""
    from apps.accounts.models import User
    admins = User.objects.filter(user_type='admin')
    admin_emails = [admin.email for admin in admins if admin.email]
    
    if admin_emails:
        subject = f"Low Stock Alert: {product.name}"
        message = f"""
        Low stock alert for product:
        
        Product: {product.name}
        Current Stock: {product.stock_quantity} {product.unit}
        Low Stock Threshold: {product.low_stock_threshold} {product.unit}
        
        Please restock this product soon.
        """
        
        send_email_notification.delay(subject, message, admin_emails)