from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import UserGroup

admin.site.register(UserGroup)


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'uuid')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'group'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


# Register the User model with the custom admin class
admin.site.register(User, CustomUserAdmin)
