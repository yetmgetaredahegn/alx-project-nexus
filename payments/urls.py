from django.urls import path
from .views import (
    initiate_payment,
    chapa_webhook,
    PaymentListView,
    PaymentDetailView,
)

app_name = "payments"

urlpatterns = [
    path("initiate/", initiate_payment, name="payment-initiate"),
    path("webhook/", chapa_webhook, name="payment-webhook"),
    path("", PaymentListView.as_view(), name="payment-list"),
    path("<uuid:pk>/", PaymentDetailView.as_view(), name="payment-detail"),
]
