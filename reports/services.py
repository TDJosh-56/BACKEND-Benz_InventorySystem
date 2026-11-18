"""Report calculations. Mirrors the logic of the Flutter ReportsScreen."""
import re
from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from inventory.models import Ingredient, InventoryTransaction
from production.models import ProductionRecord

ALLOWED_RANGES = (7, 30, 90, 180, 365)
DEFAULT_DAYS = 30

# Same keyword rules as the frontend's _categories map. First match wins.
CATEGORY_KEYWORDS = {
    'Flour and Grains': ['flour', 'oat', 'grain'],
    'Dairy': ['milk', 'butter', 'cream', 'cheese'],
    'Sugar and Sweeteners': ['sugar', 'syrup', 'honey'],
    'Fruits and Flavorings': ['strawberry', 'blueberry', 'vanilla', 'matcha', 'chocolate'],
}
OTHER_CATEGORY = 'Others'

STATUS_LABELS = {'In Stock': 'Normal', 'Low Stock': 'Low', 'Out of Stock': 'Out'}


def parse_days(raw):
    """Returns a valid range in days, or raises ValueError."""
    if raw in (None, ''):
        return DEFAULT_DAYS
    try:
        days = int(raw)
    except (TypeError, ValueError):
        raise ValueError('days must be a whole number.')
    if days not in ALLOWED_RANGES:
        raise ValueError(f'days must be one of {", ".join(map(str, ALLOWED_RANGES))}.')
    return days


def date_window(days):
    today = timezone.localdate()
    return today - timedelta(days=days - 1), today


def category_for(name):
    lower = name.lower()
    for category, words in CATEGORY_KEYWORDS.items():
        # keyword must START a word: "oat" matches "Oats" but not "Goat Milk"
        if any(re.search(r'\b' + re.escape(w), lower) for w in words):
            return category
    return OTHER_CATEGORY


def _num(value):
    value = float(value)
    return int(value) if value == round(value) else round(value, 2)


def get_records(start_date):
    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start_date, time.min), tz)
    return list(ProductionRecord.objects.filter(timestamp__gte=start_dt).order_by('timestamp'))


def calculate_usage(start_date, ingredients):
    """{ingredient_id: Decimal used} in each ingredient's stock unit.

    Read straight from the stock ledger: every production already wrote a
    negative InventoryTransaction, so this always ties out with stock, even if
    a recipe is later renamed, deleted or edited."""
    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start_date, time.min), tz)
    rows = (InventoryTransaction.objects
            .filter(transaction_type=InventoryTransaction.Type.PRODUCTION,
                    created_at__gte=start_dt,
                    ingredient_id__in=[i.pk for i in ingredients])
            .values('ingredient_id')
            .annotate(total=Sum('quantity_change')))
    return {r['ingredient_id']: -r['total'] for r in rows}


def production_series(records, days, start_date):
    """Daily buckets up to 30 days, weekly up to 180, bi-weekly for a year."""
    size = 1 if days <= 30 else (7 if days <= 180 else 14)
    count = -(-days // size)
    values = [0] * count
    for rec in records:
        idx = (timezone.localtime(rec.timestamp).date() - start_date).days
        if idx < 0:
            continue
        values[min(idx // size, count - 1)] += rec.quantity
    return [
        {'date': (start_date + timedelta(days=i * size)).isoformat(), 'units': v}
        for i, v in enumerate(values)
    ], size


def build_report(days=DEFAULT_DAYS, status_filter=None):
    start, end = date_window(days)
    ingredients = list(Ingredient.objects.filter(is_active=True).order_by('name'))
    records = get_records(start)
    usage = calculate_usage(start, ingredients)

    total = sum(r.quantity for r in records)
    counts = {'in_stock': 0, 'low_stock': 0, 'out_of_stock': 0}
    key_for = {'In Stock': 'in_stock', 'Low Stock': 'low_stock', 'Out of Stock': 'out_of_stock'}
    cat_counts = defaultdict(int)
    usage_rows = []
    for ing in ingredients:
        status = ing.status
        counts[key_for[status]] += 1
        cat_counts[category_for(ing.name)] += 1
        used = usage.get(ing.pk, Decimal(0))
        usage_rows.append({
            'ingredient_id': ing.pk,
            'name': ing.name,
            'used': _num(used),
            'unit': ing.unit,
            'current_stock': _num(ing.current_stock),
            'status': status,
            'status_label': STATUS_LABELS[status],
            'category': category_for(ing.name),
        })

    if status_filter:
        wanted = status_filter.lower()
        usage_rows = [r for r in usage_rows
                      if wanted in (r['status'].lower(), r['status_label'].lower())]

    series, bucket_days = production_series(records, days, start)
    order = list(CATEGORY_KEYWORDS) + [OTHER_CATEGORY]
    n = len(ingredients)

    return {
        'range': {'days': days, 'start_date': start.isoformat(), 'end_date': end.isoformat(),
                  'generated_at': timezone.now().isoformat()},
        'summary': {
            'total_production': total,
            'ingredients_used': sum(1 for v in usage.values() if v > 0),
            'low_stock_items': counts['low_stock'] + counts['out_of_stock'],
        },
        'production_over_time': {'bucket_days': bucket_days, 'total': total, 'data': series},
        'ingredient_usage': {'count': len(usage_rows), 'total_ingredients': n, 'items': usage_rows},
        'inventory_status': {**counts, 'total': n},
        'stock_by_category': [
            {'category': c, 'count': cat_counts[c], 'share': round(cat_counts[c] / n, 4) if n else 0}
            for c in order if cat_counts.get(c)
        ],
        'production_line_items': len(records),
    }