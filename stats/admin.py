from django.contrib import admin

from stats.models import UserStats


# Register your models here.

class UserStatsAdmin(admin.ModelAdmin):
    ordering = ('created_at',)
    list_display = ('user', 'chars', 'created_at')
    list_filter = ('user__group', 'created_at')


admin.site.register(UserStats, UserStatsAdmin)
