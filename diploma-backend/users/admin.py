from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'fullName', 'phone', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'fullName', 'phone')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('fullName', 'phone', 'avatar')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('fullName', 'phone', 'avatar')
        }),
    )
