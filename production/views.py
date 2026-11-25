from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from audit.services import Category, Delta, log
from inventory.services import deduct_stock
from recipe.models import Recipe
from .models import ProductionRecord
from .serializers import ProductionRecordSerializer


class ProductionRecordViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ProductionRecord.objects.all().order_by('-timestamp')
    serializer_class = ProductionRecordSerializer
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def _process_items(self, items_data):
        order_ref = f'ORD-{int(timezone.now().timestamp() * 1000)}'
        resolved = []
        aggregated_needs = []

        for entry in items_data:
            ser = self.get_serializer(data=entry)
            ser.is_valid(raise_exception=True)
            name = ser.validated_data['recipe_name'].strip()
            qty = ser.validated_data['quantity']

            recipe = Recipe.objects.filter(name__iexact=name).first()
            if not recipe:
                raise ValueError(f'Recipe "{name}" not found.')
            if recipe.is_archive:
                raise ValueError(f'Archived recipe "{recipe.name}" cannot be produced.')

            lines = list(recipe.recipe_ingredients.all())
            if not lines:
                raise ValueError(f'Recipe "{recipe.name}" has no ingredients configured.')

            for line in lines:
                aggregated_needs.append((line.ingredient_id, line.quantity * qty, line.unit))

            resolved.append((recipe, qty, ser.validated_data.get('comment')))

        # Deduct all ingredients atomically across the entire cart
        deduct_stock(aggregated_needs, reference=order_ref, description='Production')

        created_records = []
        for recipe, qty, comment in resolved:
            record = ProductionRecord.objects.create(
                recipe_name=recipe.name,
                quantity=qty,
                comment=comment,
            )
            log(
                Category.PRODUCTION,
                'Production confirmed',
                record.recipe_name,
                f'-{record.quantity} produced',
                Delta.NEGATIVE,
                production=record,
            )
            created_records.append(record)

        return order_ref, created_records

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        is_batch = isinstance(request.data, dict) and 'items' in request.data
        items_data = request.data['items'] if is_batch else [request.data]

        if not items_data:
            return Response({'detail': 'Add a product to the order.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order_id, records = self._process_items(items_data)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serialized = self.get_serializer(records, many=True).data
        if is_batch:
            return Response({'order_id': order_id, 'records': serialized}, status=status.HTTP_201_CREATED)
        return Response(serialized[0], status=status.HTTP_201_CREATED)


    @transaction.atomic
    def perform_update(self, serializer):
        old_quantity = serializer.instance.quantity
        record = serializer.save()
        log(
            Category.PRODUCTION,
            'Production log edited',
            f'{record.recipe_name}: {record.comment}',
            f'{old_quantity} -> {record.quantity} units',
            Delta.NEUTRAL,
            production=record,
        )
