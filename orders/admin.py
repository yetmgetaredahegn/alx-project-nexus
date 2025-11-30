from django.contrib import admin
from .models import Order

# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "total_amount", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["id", "user", "status", "total_amount", "created_at"]
    fields = ["id", "user", "status", "total_amount", "created_at"]
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ["status"]
    list_display_links = ["id", "user"]
    list_select_related = ["user"]