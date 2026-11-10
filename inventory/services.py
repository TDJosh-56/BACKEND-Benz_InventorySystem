from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.utils import timezone

from .models import Ingredient, InventoryTransaction as Tx
from .units import convert

_Q = Decimal('0.0001')


def to_decimal(value):
    return Decimal(str(value)).quantize(_Q, rounding=ROUND_HALF_UP)


@transaction.atomic
def record_change(ingredient, new_stock, tx_type, description='', reference=''):
    new_stock = to_decimal(new_stock)
    previous = ingredient.current_stock
    ingredient.current_stock = new_stock
    ingredient.save(update_fields=['current_stock', 'updated_at'])
    return Tx.objects.create(
        ingredient=ingredient, transaction_type=tx_type,
        quantity_change=new_stock - previous, previous_stock=previous,
        new_stock=new_stock, description=description, reference=reference)


@transaction.atomic
def adjust_stock(ingredient_id, delta, tx_type=Tx.Type.ADJUSTMENT, description='', reference=''):
    ing = Ingredient.objects.select_for_update().get(pk=ingredient_id)
    new_stock = ing.current_stock + to_decimal(delta)
    if new_stock < 0:
        raise ValueError(f'Not enough {ing.name} in stock.')
    return record_change(ing, new_stock, tx_type, description, reference)


def bulk_history(ingredient_ids, days=7):
    ids = list(ingredient_ids)
    if not ids:
        return {}
    tz = timezone.get_current_timezone()
    today = timezone.localdate()
    day_ends = [
        datetime.combine(today - timedelta(days=off - 1), time.min, tzinfo=tz)
        for off in range(days - 1, -1, -1)
    ]
    window_start = day_ends[0] - timedelta(days=1)

    latest_before = Tx.objects.filter(
        ingredient=OuterRef('pk'), created_at__lt=window_start
    ).order_by('-created_at', '-id').values('new_stock')[:1]
    baseline = dict(Ingredient.objects.filter(pk__in=ids)
                    .annotate(b=Subquery(latest_before)).values_list('pk', 'b'))

    in_window = {}
    for t in Tx.objects.filter(ingredient_id__in=ids, created_at__gte=window_start).order_by('created_at', 'id'):
        in_window.setdefault(t.ingredient_id, []).append(t)

    result = {}
    for pk in ids:
        txs, value, i, series = in_window.get(pk, []), baseline.get(pk), 0, []
        for end in day_ends:
            while i < len(txs) and txs[i].created_at < end:
                value = txs[i].new_stock
                i += 1
            if value is not None:
                series.append(((end - timedelta(days=1)).date(), float(value)))
        result[pk] = series
    return result
