from django.core.management.base import BaseCommand

from inventory.models import Ingredient
from inventory.serializers import IngredientSerializer

SEED = [
    ('Espresso Beans', 2.5, 5.0, 'kg'), ('Oat Meal', 4.0, 8.0, 'L'), ('Sugar', 18.0, 8.0, 'kg'),
    ('Whole Milk', 10.0, 3.0, 'L'), ('Flour', 24.5, 10.0, 'kg'), ('Butter', 12.2, 5.0, 'kg'),
    ('Eggs', 10.5, 4.0, 'Pcs'), ('Chocolate Syrup', 9.5, 10.0, 'L'), ('Vanilla Syrup', 5.7, 6.0, 'L'),
    ('Strawberry Puree', 8.2, 10.0, 'L'), ('Blueberry Puree', 5.3, 3.0, 'L'), ('Matcha', 30.0, 5.0, 'kg'),
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        n = 0
        for name, stock, threshold, unit in SEED:
            if Ingredient.objects.filter(name__iexact=name, is_active=True).exists():
                continue
            s = IngredientSerializer(data={'ingredient': name, 'stock': stock, 'threshold': threshold, 'unit': unit})
            s.is_valid(raise_exception=True)
            s.save()
            n += 1
        self.stdout.write(f'Seeded {n} ingredient(s).')
