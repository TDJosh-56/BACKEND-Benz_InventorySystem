from rest_framework import status as http
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ingredient
from .serializers import IngredientSerializer
from .services import bulk_history


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = Ingredient.objects.filter(is_active=True)
        p = self.request.query_params
        if p.get('search'):
            qs = qs.filter(name__icontains=p['search'].strip())
        if p.get('category'):
            qs = qs.filter(category__iexact=p['category'].strip())
        return qs.order_by('name')

    def list(self, request, *args, **kwargs):
        items = list(self.get_queryset())
        ctx = self.get_serializer_context()
        ctx['history_map'] = bulk_history([i.pk for i in items])
        return Response(IngredientSerializer(items, many=True, context=ctx).data)

    def destroy(self, request, *args, **kwargs):
        ing = self.get_object()
        if ing.recipe_lines.exists():
            return Response({'status': 'error', 'message': 'This ingredient is used by a recipe.'},
                            status=http.HTTP_409_CONFLICT)
        ing.is_active = False
        ing.save(update_fields=['is_active', 'updated_at'])
        return Response({'status': 'success', 'message': 'Ingredient successfully deleted.'})

    @action(detail=True, methods=['get'], url_path='stock-history')
    def stock_history(self, request, pk=None):
        ing = self.get_object()
        series = bulk_history([ing.pk]).get(ing.pk, [])
        return Response({
            'metric': 'End-of-Day Stock',
            'data': [{'date': d.isoformat(), 'stock': v} for d, v in series],
        })