from django.contrib import admin

from .models import User


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "country", "gender", "app_role", "created_at")
    list_filter = ("app_role", "gender", "country")
    search_fields = ("username", "email")
    readonly_fields = ("created_at", "updated_at", "last_login")
