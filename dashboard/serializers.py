from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    total_ingredients = serializers.IntegerField()
    total_materials = serializers.IntegerField()
    low_stock_alerts = serializers.IntegerField()
    out_of_stock_alerts = serializers.IntegerField()
    production_today = serializers.IntegerField()


class StockItemSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField()
    name = serializers.CharField()
    current_stock = serializers.FloatField()
    unit = serializers.CharField()
    status = serializers.CharField()


class StockOverviewSerializer(serializers.Serializer):
    in_stock = serializers.IntegerField()
    low_stock = serializers.IntegerField()
    out_of_stock = serializers.IntegerField()
    total = serializers.IntegerField()


class DashboardSerializer(serializers.Serializer):
    summary = DashboardSummarySerializer()
    stock_alerts = StockItemSerializer(many=True)
    stock_levels = StockItemSerializer(many=True)
    stock_overview = StockOverviewSerializer()