from django.db.models import Sum
from django.utils import timezone

from inventory.models import Ingredient
from production.models import ProductionRecord


def get_inventory_items():
    return list(
        Ingredient.objects.filter(is_active=True)
    )


def get_stock_status_counts(Ingredient):
    counts = {
        'in_stock': 0,
        'low_stock': 0,
        'out_of_stock': 0,
    }

    for item in Ingredient:
        if item.status == 'In Stock':
            counts['in_stock'] += 1
        elif item.status == 'Low Stock':
            counts['low_stock'] += 1
        elif item.status == 'Out of Stock':
            counts['out_of_stock'] += 1

    return counts


def get_production_today():
    today = timezone.localdate()

    total = ProductionRecord.objects.filter(
        timestamp__date=today
    ).aggregate(
        total=Sum('quantity')
    )['total']

    return total or 0


def get_stock_item_data(item):
    return {
        'ingredient_id': item.pk,
        'name': item.name,
        'current_stock': float(item.current_stock),
        'unit': item.unit,
        'status': item.status,
    }

def get_dashboard_data():
    inventory = get_inventory_items()

    stock_counts = get_stock_status_counts(inventory)

    stock_alerts = [
        get_stock_item_data(item)
        for item in inventory
        if item.status in ('Low Stock', 'Out of Stock')
    ]

    stock_levels = [
        get_stock_item_data(item)
        for item in inventory
    ]

    return {
        'summary': {
            'total_inventory': len(inventory),
            'low_stock_alerts': stock_counts['low_stock'],
            'out_of_stock_alerts': stock_counts['out_of_stock'],
            'production_today': get_production_today(),
        },
        'stock_alerts': stock_alerts,
        'stock_levels': stock_levels,
        'stock_overview': {
            **stock_counts,
            'total': len(inventory),
        },
    }