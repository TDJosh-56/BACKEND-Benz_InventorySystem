from rest_framework import serializers

from recipe.models import Recipe
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Read shape - matches the Flutter `AuditLogEntry` model."""
    id = serializers.SerializerMethodField()
    badgeText = serializers.CharField(source='badge_text', read_only=True)
    changeLabel = serializers.CharField(source='change_label', read_only=True)
    deltaType = serializers.CharField(source='delta_type', read_only=True)
    recipeId = serializers.IntegerField(source='recipe_id', read_only=True)
    ingredientId = serializers.IntegerField(source='ingredient_id', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'timestamp', 'category', 'badgeText', 'title', 'subtitle',
                  'changeLabel', 'deltaType', 'recipeId', 'ingredientId']

    def get_id(self, obj):
        return f'LOG-{obj.pk:06d}'


class AuditLogCreateSerializer(serializers.Serializer):
    """Write shape - for events the backend cannot see itself (e.g. production)."""
    category = serializers.ChoiceField(choices=AuditLog.Category.choices)
    title = serializers.CharField(max_length=120)
    subtitle = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    changeLabel = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    deltaType = serializers.ChoiceField(choices=AuditLog.Delta.choices, default=AuditLog.Delta.NEUTRAL)
    recipeId = serializers.PrimaryKeyRelatedField(
        source='recipe', queryset=Recipe.objects.all(), required=False, allow_null=True)

    def create(self, validated_data):
        # The server stamps the time - clients cannot back-date audit entries.
        return AuditLog.objects.create(
            category=validated_data['category'],
            title=validated_data['title'].strip(),
            subtitle=validated_data['subtitle'].strip(),
            change_label=validated_data['changeLabel'].strip(),
            delta_type=validated_data['deltaType'],
            recipe=validated_data.get('recipe'),
        )
