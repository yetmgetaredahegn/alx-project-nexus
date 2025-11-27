from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task(bind=True, max_retries=3)
def send_payment_confirmation_email(self, email, amount, tx_ref):
    subject = "Payment Successful"
    message = (
        f"Your payment of {amount} ETB was successful.\n"
        f"Transaction Ref: {tx_ref}"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
