from rest_framework import serializers
from .models import ProductionRecord

class ProductionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionRecord
        fields = '__all__'  # This automatically safely packages all your columns into JSON
