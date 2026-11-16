from django.urls import path

from . import views

urlpatterns = [
    path('', views.report, name='report'),
    path('summary/', views.summary, name='report-summary'),
    path('production-over-time/', views.production_over_time, name='report-production'),
    path('ingredient-usage/', views.ingredient_usage, name='report-usage'),
    path('inventory-status/', views.inventory_status, name='report-status'),
    path('stock-by-category/', views.stock_by_category, name='report-categories'),
    path('export/', views.export_csv, name='report-export'),
]