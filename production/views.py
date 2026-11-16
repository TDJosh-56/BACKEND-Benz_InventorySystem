from rest_framework import viewsets, mixins 
from .models import ProductionRecord
from .serializers import ProductionRecordSerializer

class ProductionRecordViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = ProductionRecord.objects.all().order_by('-timestamp')
    serializer_class = ProductionRecordSerializer