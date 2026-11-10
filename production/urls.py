from django.urls import path, include 
from rest_framework.routers import DefaultRouter
from .views import ProductionRecordViewSet

router = DefaultRouter()

router.register(r'records', ProductionRecordViewSet, basename='production-record')

urlpatterns = [
    path('', include(router.urls)),
]