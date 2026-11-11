from django.db.models import Sum
from django.utils import timezone

from inventory.models import Ingredient
from production.models import ProductionRecord


def get_inventory_summary():
    ingredients = list(
        Ingredient.objects.filter(is_active=True)
    )

    total = len(ingredients)

    low_stock = sum(
        ingredient.status == 'Low Stock'
        for ingredient in ingredients
    )

    out_of_stock = sum(
        ingredient.status == 'Out of Stock'
        for ingredient in ingredients
    )

    return {
        'total_ingredients': total,
        'low_stock_ingredients': low_stock,
        'out_of_stock_ingredients': out_of_stock,
        'in_stock_ingredients': total - low_stock - out_of_stock,
    }


def get_production_today():
    today = timezone.localdate()

    total = ProductionRecord.objects.filter(
        timestamp__date=today
    ).aggregate(
        total=Sum('quantity')
    )['total']

    return total or 0


def get_stock_alerts():
    ingredients = Ingredient.objects.filter(is_active=True)

    alerts = []

    for ingredient in ingredients:
        if ingredient.status != 'In Stock':
            alerts.append({
                'ingredient_id': ingredient.pk,
                'ingredient': ingredient.name,
                'stock': float(ingredient.current_stock),
                'unit': ingredient.unit,
                'threshold': float(ingredient.threshold_in_stock_unit),
                'status': ingredient.status,
            })

    return alerts


def get_stock_levels():
    ingredients = Ingredient.objects.filter(is_active=True)

    return [
        {
            'ingredient_id': ingredient.pk,
            'ingredient': ingredient.name,
            'stock': float(ingredient.current_stock),
            'unit': ingredient.unit,
            'status': ingredient.status,
        }
        for ingredient in ingredients
    ]


def get_dashboard_data():
    return {
        'summary': get_inventory_summary(),
        'production_today': get_production_today(),
        'stock_alerts': get_stock_alerts(),
        'stock_levels': get_stock_levels(),
    }