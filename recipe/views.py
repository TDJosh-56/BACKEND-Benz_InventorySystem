from django.shortcuts import render
from .serializer import RecipeSerializer, SubcategorySerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Recipe, Subcategory
from django.db.models import Q, Count
from rest_framework import status

@api_view(['GET'])
def get_subcategories(request):
    if request.method == 'GET':
        subcategories = Subcategory.objects.annotate(recipe_count=Count('recipes')).order_by('-recipe_count')
        serializer = SubcategorySerializer(subcategories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
def get_recipe(request):
    
    if request.method == 'GET':
        status_filter = request.GET.get('status')
        search = request.GET.get('search')
        category = request.GET.get('category')
        subcategory = request.GET.get('subcategory')

        recipes = Recipe.objects.all().order_by('-name')

        if status_filter:
            if status_filter.lower() == 'archived':
                recipes = recipes.filter(is_archive=True)
            elif status_filter.lower() == 'active':
                recipes = recipes.filter(is_archive=False)

        if search:
            recipes = recipes.filter(
                Q(name__icontains=search) | Q(description__icontains=search) | Q(ingredients__name__icontains=search).distinct()
            )

        if category:
            recipes = recipes.filter(category__iexact=category.strip())

        if subcategory:
            recipes = recipes.filter(subcategory__name__iexact=subcategory.strip())
        
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = RecipeSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PATCH':
        serializer = RecipeSerializer(recipes, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # DELETE EVENT
    elif request.method == 'DELETE':
        recipes.delete()

        return Response(
            {"message": "Recipe deleted successfully"},
            status=status.HTTP_200_OK
        )