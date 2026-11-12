from django.contrib import admin

from .models import Setting


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('autoarchiveoldrecipe', 'allow_production_override')
    exclude = ('passcode_hash', 'recovery_code_hash')  # never expose credential hashes

    def has_add_permission(self, request):
        return not Setting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False