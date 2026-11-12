from django.urls import path
from dashboard import views

urlpatterns = [
    path('dashboard/', views.summary, name='dashboard_summary'),
]