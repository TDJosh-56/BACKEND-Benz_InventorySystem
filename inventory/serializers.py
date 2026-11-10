from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from rest_framework import serializers

from .models import Ingredient, InventoryTransaction
from .services import bulk_history, record_change, to_decimal
from .units import UNITS, compatible, convert


class QuantityField(serializers.FloatField):
    def __init__(self, **kwargs):
        kwargs.setdefault('min_value', 0)
        kwargs.setdefault('max_value', 999_999_999)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        return to_decimal(super().to_internal_value(data))

    def to_representation(self, value):
        return float(value)


class CostField(QuantityField):
    def to_internal_value(self, data):
        return Decimal(str(serializers.FloatField.to_internal_value(self, data))).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)


class IngredientSerializer(serializers.ModelSerializer):
    ingredient_id = serializers.IntegerField(source='pk', read_only=True)
    ingredient = serializers.CharField(source='name', max_length=100)
    stock = QuantityField(source='current_stock', required=False)
    threshold = QuantityField(source='reorder_threshold', required=False)
    unit = serializers.ChoiceField(choices=UNITS)
    threshold_unit = serializers.ChoiceField(source='reorder_unit', choices=UNITS, required=False)
    cost_item = CostField(required=False, allow_null=True)
    category = serializers.ChoiceField(choices=[c[0] for c in Ingredient.CATEGORY_CHOICES], required=False)
    status = serializers.SerializerMethodField()
    history_7_days = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ['ingredient_id', 'ingredient', 'stock', 'unit', 'threshold', 'threshold_unit',
                  'cost_item', 'category', 'status', 'history_7_days']

    def to_internal_value(self, data):
        data = data.copy()
        for alias in ('cost_Item', 'costItem'):
            if alias in data and 'cost_item' not in data:
                data['cost_item'] = data[alias]
        return super().to_internal_value(data)

    def get_status(self, obj):
        return obj.status

    def get_history_7_days(self, obj):
        history = self.context.get('history_map')
        if history is None:
            history = bulk_history([obj.pk])
        series = history.get(obj.pk)
        return [v for _, v in series] if series else [float(obj.current_stock)]

    def validate_ingredient(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Name is required.')
        clash = Ingredient.objects.filter(is_active=True, name__iexact=value)
        if self.instance:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError('An ingredient with this name already exists.')
        return value

    def validate(self, attrs):
        inst = self.instance
        unit = attrs.get('unit', inst.unit if inst else None)
        reorder_unit = attrs.get('reorder_unit', inst.reorder_unit if inst else unit)
        if unit and reorder_unit and not compatible(reorder_unit, unit):
            raise serializers.ValidationError({
                'threshold_unit': f'Cannot compare {reorder_unit} with {unit}. '
                                  'Use the same type of unit (weight, volume or pieces).'})
        if not inst:
            attrs.setdefault('reorder_unit', unit)
        elif 'unit' in attrs and attrs['unit'] != inst.unit:
            for line in inst.recipe_lines.select_related('recipe'):
                if convert(1, line.unit, attrs['unit']) is None:
                    raise serializers.ValidationError({
                        'unit': f'Recipe "{line.recipe.name}" uses {line.unit}, '
                                f'which cannot be converted to {attrs["unit"]}.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        stock = validated_data.pop('current_stock', to_decimal(0))
        ing = Ingredient.objects.create(current_stock=0, **validated_data)
        record_change(ing, stock, InventoryTransaction.Type.INITIAL, description='Ingredient added')
        return ing

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = Ingredient.objects.select_for_update().get(pk=instance.pk)
        new_stock = validated_data.pop('current_stock', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if new_stock is not None and new_stock != instance.current_stock:
            record_change(instance, new_stock, InventoryTransaction.Type.ADJUSTMENT,
                          description='Stock edited')
        return instance
