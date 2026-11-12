from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, status 
from rest_framework.response import Response 
from .models import ProductionRecord
from .serializers import ProductionRecordSerializer

class ProductionRecordViewSet(viewsets.ModelViewSet):
    queryset = ProductionRecord.objects.all().order_by('-timestamp')
    serializer_serializer_class = ProductionRecordSerializer

"""    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        #to comply with flutter 7-day edit window
        seven_days_ago = timezone.now() - timedelta(days = 7)
        if instance.timestamp < seven_days_ago:
            return Response(
                {"detail": "This production record is locked. Edits are only allowed within 7 days of creation."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not instance.original_quantity:
            request.data['original_quantity'] = instance.quantity

        request.data['edited_at'] = timezone.now()

        return super().update(request, *args, **kwargs) """