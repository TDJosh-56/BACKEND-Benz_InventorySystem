from django.urls import path
from dashboard import views

urlpatterns = [
    path('', views.summary, name='dashboard_summary'),
]