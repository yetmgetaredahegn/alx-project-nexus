from django.contrib import admin
from .models import Order, OrderItem, OrderCancellationRequest

# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "payment_status", "total", "created_at"]
    list_filter = ["status", "payment_status", "created_at"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["id", "user", "total", "created_at", "updated_at"]
    fields = ["id", "user", "status", "payment_status", "payment_method", "total", "shipping_address_line", "shipping_city", "shipping_postal_code", "shipping_country", "created_at", "updated_at"]
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ["status", "payment_status"]
    list_display_links = ["id", "user"]
    list_select_related = ["user"]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related("user").prefetch_related("items")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "product_title", "quantity", "unit_price", "line_total"]
    search_fields = ["order__user__email", "product_title"]
    readonly_fields = ["id", "order", "product_id", "product_title", "unit_price", "quantity", "line_total"]
    fields = ["id", "order", "product_id", "product_title", "unit_price", "quantity", "line_total"]
    list_per_page = 20
    list_select_related = ["order", "order__user"]


@admin.register(OrderCancellationRequest)
class OrderCancellationRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "user", "reason", "handled", "created_at"]
    list_filter = ["handled", "created_at"]
    search_fields = ["order__user__email", "user__email", "reason"]
    readonly_fields = ["id", "order", "user", "created_at"]
    fields = ["id", "order", "user", "reason", "handled", "handled_at", "result_note", "created_at"]
    list_per_page = 20
    list_editable = ["handled"]
    list_select_related = ["order", "user"]