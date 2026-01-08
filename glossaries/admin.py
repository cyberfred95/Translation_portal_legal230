"""
Glossary admin module.

Admin interface is disabled because all glossaries are now stored and managed
in lara-bridge. The Glossary model in this project serves only as a cache/metadata
store for synchronization purposes via Django signals (see signals.py).

If admin access is needed for debugging or maintenance, uncomment the code below.
"""
# Admin disabled - glossaries are managed in lara-bridge
# Uncomment below if admin access is needed for debugging/maintenance:
#
# from django.contrib import admin
# from .models import Glossary
#
# @admin.register(Glossary)
# class GlossaryAdmin(admin.ModelAdmin):
#     list_display = ['name', 'user', 'source_language', 'target_language', 'domain', 'glossary_id', 'created_at']
#     list_filter = ['domain', 'source_language', 'target_language', 'created_at']
#     search_fields = ['name', 'glossary_id']
#     readonly_fields = ['glossary_id', 'created_at']
#
#     def has_add_permission(self, request):
#         return False
#
#     def has_delete_permission(self, request, obj=None):
#         return False
