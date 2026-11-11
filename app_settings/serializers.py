from rest_framework import serializers

from .models import Setting


class SettingSerializer(serializers.ModelSerializer):
    autoArchiveOldRecipes = serializers.BooleanField(source='autoarchiveoldrecipe')
    allowProductionOverride = serializers.BooleanField(source='allow_production_override')


    class Meta:
        model = Setting
        fields = ['autoArchiveOldRecipes', 'allowProductionOverride', 'updated_at']
        read_only_fields = ['updated_at']
