from django.urls import path
from recipe import views

urlpatterns = [
    path('recipes/', views.get_recipe, name='recipe-list'),
    path('subcategories/', views.get_subcategories, name='subcategory-list'),
    path('recipes/<int:pk>/', views.get_recipe_detail, name='recipe-detail'),
]