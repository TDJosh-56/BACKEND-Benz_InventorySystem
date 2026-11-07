from rest_framework import serializers
from recipe.models import Recipe

class RecipeSerializer(serializers.modelSerializer):
    status = serializers.SerializermethodField()

    class Meta:
        model = Recipe
        fields = [
            '__all__'
            ]