from rest_framework import serializers
from recipe.models import Recipe, Subcategory

class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name']

        
class RecipeSerializer(serializers.modelSerializer):
    status = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    last_used = serializers.SerializerMethodField()
    image = serializers.ImageField(required=True)
    
    class Meta:
        model = Recipe, Subcategory
        fields =  '__all__'

    def create(self, validated_data):
        subcategory_name = validated_data.pop('subcategory', None)
        recipe = Recipe.objects.create(**validated_data)

        if subcategory_name:
            clean_name = subcategory_name.strip()
            sub_obj =  Subcategory.objects.filter(name__iexact=clean_name).first()

            if not sub_obj:
                sub_obj = Subcategory.objects.create(name=clean_name)

            recipe.subcategory = sub_obj
            recipe.save()

        return recipe

    def update(self, instance, validated_data):
        subcategory_name = validated_data.pop('subcategory', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if subcategory_name:
            clean_name = subcategory_name.strip()
            sub_obj = Subcategory.objects.filter(name__iexact=clean_name).first()

            if not sub_obj:
                sub_obj = Subcategory.objects.create(name=clean_name)

            instance,self.subcategory= sub_obj
        else:
            instance.subcategory = None

        instance.save()
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