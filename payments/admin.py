from django.contrib import admin
from .models import Payment
# Register your models here.
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "tx_ref", "amount", "currency", "status", "created_at", "paid_at"]
    list_filter = ["status", "created_at", "paid_at"]
    search_fields = ["order__user__email", "order__user__first_name", "order__user__last_name", "tx_ref"]
    readonly_fields = ["id", "order", "tx_ref", "amount", "currency", "created_at", "paid_at"]
    fields = ["id", "order", "tx_ref", "amount", "currency", "status", "created_at", "paid_at"]
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ["status"]  # Status can be edited in list view
    list_display_links = ["id", "order"]
    list_select_related = ["order"]