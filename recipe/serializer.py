from rest_framework import serializers
from recipe.models import Recipe, Subcategory, RecipeIngredient
from django.db import transaction
from inventory.models import Ingredient

class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name']

class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredientId = serializers.PrimaryKeyRelatedField(source='ingredient', queryset=Ingredient.objects.all())
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    
    class Meta:
        model = RecipeIngredient
        fields =  ['ingredientId', 'ingredient_name', 'quantity', 'unit']


class RecipeSerializer(serializers.ModelSerializer):
    subcategory = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=30)
    isArchived = serializers.BooleanField(source='is_archive', default=False)
    yieldAmount = serializers.IntegerField(source='yield_per_batch')
    yieldUnit = serializers.CharField(source='yield_unit')
    ingredients = RecipeIngredientSerializer(source='recipe_ingredients', many=True, required=False)
    
    class Meta:
        model = Recipe
        fields =  [
            'id', 'name', 'category', 'subcategory', 'price', 
            'yieldAmount', 'yieldUnit', 'description', 'isArchived', 
            'image', 'ingredients'
        ]

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