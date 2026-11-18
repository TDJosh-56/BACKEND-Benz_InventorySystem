from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from audit.models import AuditLog
from inventory.models import Ingredient
from production.models import ProductionRecord
from recipe.models import Recipe, RecipeIngredient
from reports.services import build_report, category_for


class ProductionStockTests(TestCase):
    def setUp(self):
        self.c = APIClient()
        self.flour = Ingredient.objects.create(
            name='Flour', current_stock=10, unit='kg', reorder_unit='kg')
        self.bread = Recipe.objects.create(
            name='Bread', category='food', yield_per_batch=1,
            yield_unit='pcs', price=5, description='x')
        # 500 g per bread, while stock is kept in kg -> tests unit conversion
        RecipeIngredient.objects.create(
            recipe=self.bread, ingredient=self.flour, quantity=500, unit='g')

    def produce(self, name='Bread', qty=3):
        return self.c.post('/api/production/records/',
                           {'recipe_name': name, 'quantity': qty}, format='json')

    def test_deducts_stock_with_unit_conversion(self):
        self.assertEqual(self.produce(qty=3).status_code, 201)
        self.flour.refresh_from_db()
        self.assertEqual(self.flour.current_stock, Decimal('8.5'))   # 10 - 1.5 kg

    def test_not_enough_stock_changes_nothing(self):
        r = self.produce(qty=50)                                      # needs 25 kg
        self.assertEqual(r.status_code, 400)
        self.assertIn('Not enough Flour', r.json()['detail'])
        self.flour.refresh_from_db()
        self.assertEqual(self.flour.current_stock, 10)
        self.assertEqual(ProductionRecord.objects.count(), 0)

    def test_unknown_recipe_is_recorded_without_deduction(self):
        self.assertEqual(self.produce(name='Mystery', qty=2).status_code, 201)
        self.flour.refresh_from_db()
        self.assertEqual(self.flour.current_stock, 10)

    def test_quantity_must_be_positive(self):
        for bad in (0, -5):
            self.assertEqual(self.produce(qty=bad).status_code, 400)
        self.assertEqual(ProductionRecord.objects.count(), 0)

    def test_audit_entry_written(self):
        self.produce(qty=3)
        self.assertTrue(AuditLog.objects.filter(
            category='production', change_label='3 produced').exists())

    def test_report_usage_matches_stock_drop(self):
        self.produce(qty=3)
        self.flour.refresh_from_db()
        row = build_report(30)['ingredient_usage']['items'][0]
        self.assertEqual(row['used'], 1.5)
        self.assertEqual(row['current_stock'], 8.5)

    def test_category_fix(self):
        self.assertEqual(category_for('Goat Milk'), 'Dairy')
        self.assertEqual(category_for('Oats'), 'Flour and Grains')

    def test_report_survives_recipe_rename_and_edit(self):
        self.produce(qty=3)
        self.bread.name = 'Sourdough'          # rename
        self.bread.save()
        RecipeIngredient.objects.filter(recipe=self.bread).update(quantity=999)  # edit
        row = build_report(30)['ingredient_usage']['items'][0]
        self.assertEqual(row['used'], 1.5)     # history unchanged