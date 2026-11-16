from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'category', 'title', 'subtitle', 'change_label', 'delta_type')
    list_filter = ('category', 'delta_type')
    search_fields = ('title', 'subtitle')
    date_hierarchy = 'timestamp'

    # append-only trail
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
