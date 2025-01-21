from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ResetPasswordCode
from .models import UserGroup


class UserGroupAdmin(admin.ModelAdmin):
    fields = ['name', 'api_key', 'admin']


admin.site.register(UserGroup, UserGroupAdmin)


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'uuid')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'group'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ['uuid']


# Register the User model with the custom admin class
admin.site.register(User, CustomUserAdmin)

admin.site.register(ResetPasswordCode)
