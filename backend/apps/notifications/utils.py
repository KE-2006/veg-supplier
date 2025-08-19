from django.core.mail import send_mail

def send_email_notification(subject, message, recipient_email):
    send_mail(
        subject,
        message,
        'no-reply@freshproduce.com',
        [recipient_email],
        fail_silently=False,
    )
