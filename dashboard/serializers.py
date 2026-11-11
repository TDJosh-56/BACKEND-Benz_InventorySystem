from rest_framework import serializers

class DashboardSerializer(serializers.Serializer):
    total_ingredients = serializers.IntegerField()
    low_stock_ingredients = serializers.IntegerField()
    out_of_stock_ingredients = serializers.IntegerField()