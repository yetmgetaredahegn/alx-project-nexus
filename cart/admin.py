from django.contrib import admin
from .models import Cart, CartItem  
# Register your models here.
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "total", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["id", "user", "total", "created_at", "updated_at"]
    fields = ["id", "user", "total", "created_at", "updated_at"]
    list_per_page = 10
    list_max_show_all = 100
    # Note: 'total' is a @property, not a database field, so it cannot be in list_editable
    list_editable = []  # No editable fields since total is a property
    list_display_links = ["id", "user"]
    list_select_related = ["user"]
    list_prefetch_related = ["items", "items__product"]



@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["id", "cart", "product", "quantity", "unit_price", "line_total", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["cart__user__email", "cart__user__first_name", "cart__user__last_name", "product__title"]
    readonly_fields = ["id", "cart", "product", "unit_price", "line_total", "created_at", "updated_at"]
    fields = ["id", "cart", "product", "quantity", "unit_price", "line_total", "created_at", "updated_at"]
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ["quantity"]  # Only quantity can be edited
    list_display_links = ["id", "cart", "product"]
    list_select_related = ["cart", "product", "cart__user"]    