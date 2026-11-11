from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .services import get_dashboard_data
from .serializers import DashboardSerializer


@api_view(['GET'])
def summary(self, request):
    data = get_dashboard_data()

    serializer = DashboardSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.data)