from rest_framework import serializers
from recipe.models import Recipe, Subcategory, RecipeIngredient
from django.db import transaction
from inventory.models import Ingredient
import json
import base64, uuid
from django.core.files.base import ContentFile
from rest_framework.fields import SkipField, empty
from recipe.models import validate_image_size
from inventory.units import UNITS, compatible


class Base64ImageField(serializers.ImageField):
    def validate_empty_values(self, data):
        if data is empty:
            raise SkipField()
        if data is None or data == '':
            return (True, None)
        return super().validate_empty_values(data)

    def to_internal_value(self, data):
        if isinstance(data, str):
            if data.startswith('data:image'):
                try:
                    header, b64 = data.split(';base64,', 1)
                    ext = header.split('/')[-1].replace('jpeg', 'jpg')
                    data = ContentFile(
                        base64.b64decode(b64),
                        name=f'{uuid.uuid4().hex[:12]}.{ext}',
                    )
                except Exception:
                    raise serializers.ValidationError('Invalid image data.')
            elif data.startswith(('http://', 'https://')):
                raise SkipField()
        return super().to_internal_value(data)
    
class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name']

class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredientId = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.filter(is_active=True), pk_field=serializers.CharField())
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    category = serializers.CharField(source='ingredient.category', read_only=True)
    quantity = serializers.FloatField(min_value=0.0001)
    unit = serializers.ChoiceField(choices=UNITS)

    class Meta:
        model = RecipeIngredient
        fields = ['ingredientId', 'ingredient_name', 'category', 'quantity', 'unit']

    def validate(self, attrs):
        ingredient, unit = attrs['ingredient'], attrs['unit']
        if not compatible(unit, ingredient.unit):
            raise serializers.ValidationError({
                'unit': f'{unit} cannot be converted to {ingredient.unit}, '
                        f'the stock unit of {ingredient.name}.'
            })
        return attrs


CATEGORY_IN = {'food': 'food', 'drink': 'drinks', 'drinks': 'drinks'}
CATEGORY_OUT = {'food': 'Food', 'drinks': 'Drink'}

class CategoryField(serializers.Field):
    default_error_messages = {'invalid': 'Category must be "Food" or "Drink".'}

    def to_internal_value(self, data):
        value = CATEGORY_IN.get(str(data).strip().lower())
        if value is None:
            self.fail('invalid')
        return value

    def to_representation(self, value):
        return CATEGORY_OUT.get(value, value)

    
class RecipeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    category = CategoryField()
    subcategory = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=30)
    isArchived = serializers.BooleanField(source='is_archive', default=False)
    price = serializers.FloatField(min_value=0.01)
    yieldAmount = serializers.IntegerField(source='yield_per_batch', min_value=1)
    yieldUnit = serializers.CharField(source='yield_unit')
    ingredients = RecipeIngredientSerializer(source='recipe_ingredients', many=True, required=False)
    imageUrl = Base64ImageField(source='image', validators=[validate_image_size])

    class Meta:
        model = Recipe
        fields =  [
            'id', 'name', 'category', 'subcategory', 'price', 
            'yieldAmount', 'yieldUnit', 'description', 'isArchived', 
            'imageUrl', 'ingredients'
        ]


    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['subcategory'] = data.get('subcategory') or ''
        data['imageUrl'] = data.get('imageUrl') or ''
        return data
    
    def validate_ingredients(self, items):
        ids = [i['ingredient'].pk for i in items]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Duplicate ingredients are not allowed.")
        return items

    def to_internal_value(self, data):
        data = dict(data.items())

        raw = data.get('ingredients')
        if isinstance(raw, str):
            try:
                data['ingredients'] = json.loads(raw) if raw.strip() else []
            except ValueError:
                raise serializers.ValidationError({'ingredients': 'Must be valid JSON.'})

        return super().to_internal_value(data)

    @staticmethod
    def _get_or_create_subcategory(name):
        name = (name or '').strip()
        if not name:
            return None
        sub = Subcategory.objects.filter(name__iexact=name).first()
        return sub or Subcategory.objects.create(name=name)

    @staticmethod
    def _set_ingredients(recipe, items):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                quantity=item['quantity'],
                unit=item['unit'],
            )
            for item in items
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', [])
        subcategory_name = validated_data.pop('subcategory', None)
        recipe = Recipe.objects.create( subcategory=self._get_or_create_subcategory(subcategory_name), **validated_data)

        self._set_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', None)

        if 'subcategory' in validated_data:
            instance.subcategory = self._get_or_create_subcategory(validated_data.pop('subcategory'))

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()


        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._set_ingredients(instance, ingredients_data)
        return instance

    def get_last_used(self, obj):
        latest_log = obj.auditlog_set.order_by('-timestamp').first()
        if latest_log:
            return latest_log.timestamp
        return None

    def get_status(self, obj):
        if obj.is_archive:
            return "Archived"
        else:
            return "Active"