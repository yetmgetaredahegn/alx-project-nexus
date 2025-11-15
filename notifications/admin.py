# notifications/admin.py
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type", "is_sent", "created_at")
    search_fields = ("user__email", "subject", "message")
    list_filter = ("type", "is_sent", "created_at")
