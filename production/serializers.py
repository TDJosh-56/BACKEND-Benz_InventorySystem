from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import ProductionRecord


class ProductionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionRecord
        fields = '__all__'
        read_only_fields = ['id', 'timestamp', 'edited_at', 'original_quantity']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than 0.')
        return value

    def update(self, instance, validated_data):
        if timezone.now() - instance.timestamp > timedelta(days=7):
            raise serializers.ValidationError('Production logs can only be edited within 7 days.')

        comment = (validated_data.get('comment') or '').strip()
        if not comment:
            raise serializers.ValidationError({'comment': 'A reason comment is required when editing a log.'})

        new_quantity = validated_data.get('quantity', instance.quantity)
        if instance.original_quantity is None:
            instance.original_quantity = instance.quantity

        instance.quantity = new_quantity
        instance.comment = comment
        instance.edited_at = timezone.now()
        instance.save(update_fields=['quantity', 'comment', 'edited_at', 'original_quantity'])
        return instance
