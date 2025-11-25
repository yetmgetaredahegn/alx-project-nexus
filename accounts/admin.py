from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Profile

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("id", "email", "username", "is_active", "is_staff", "is_seller")
    list_filter = ("is_staff", "is_superuser", "is_active", "is_seller")
    search_fields = ("email", "username")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "is_seller", "groups")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2", "is_seller"),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone")
    search_fields = ("user__email", "user__username", "phone")
