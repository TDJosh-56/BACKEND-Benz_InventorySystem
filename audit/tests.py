from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from app_settings.models import Setting
from audit.models import AuditLog
from audit.services import Category, Delta, log, log_event
from recipe.models import Recipe
from inventory.models import Ingredient
from inventory.services import deduct_stock
from production.models import ProductionRecord


class AuditServicesTests(TestCase):
    def test_log_event_is_the_same_function(self):
        self.assertIs(log_event, log)

    def test_log_writes_one_row_with_links_and_truncates(self):
        rec = ProductionRecord.objects.create(recipe_name='Latte', quantity=1)
        entry = log(Category.PRODUCTION, 'T' * 300, 'S' * 400, 'C' * 300, Delta.NEGATIVE, production=rec)
        entry.refresh_from_db()
        self.assertEqual((len(entry.title), len(entry.subtitle), len(entry.change_label)), (120, 255, 120))
        self.assertEqual((entry.category, entry.delta_type, entry.production_id), ('production', 'negative', rec.pk))
        self.assertEqual(entry.badge_text, 'PRODUCTION')
        self.assertEqual(AuditLog.objects.count(), 1)

    def test_log_can_link_the_settings_row(self):
        s = Setting.load()
        self.assertEqual(log(Category.SETTINGS, 'Settings updated', settings=s).settings_id, s.pk)


class AuditHooksTests(TestCase):
    def setUp(self):
        self.c = APIClient()
        
    def logs(self):
        return list(AuditLog.objects.order_by('id'))
    
    def last(self):
        return self.logs()[-1]
        
    def make_ingredient(self, **over):
        body = {'ingredient': 'Flour', 'stock': 10, 'unit': 'kg', 'threshold': 2}
        body.update(over)
        r = self.c.post('/api/ingredients/', body, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        return Ingredient.objects.get(pk=r.json()['ingredient_id'])

    def test_ingredient_add_edit_delete_are_logged(self):
        ing = self._ingredient()
        self.assertEqual(AuditLog.objects.filter(category='inventory', ingredient=ing).count(), 1)
        self.c.patch(f'/api/ingredients/{ing.pk}/', {'stock': 4}, format='json')
        last = AuditLog.objects.filter(ingredient=ing).first()
        self.assertEqual(last.delta_type, 'negative')
        self.assertEqual(last.change_label, '10 -> 4 kg')
        self.c.delete(f'/api/ingredients/{ing.pk}/')
        self.assertEqual(AuditLog.objects.filter(ingredient=ing).first().title, 'Flour')
        self.assertEqual(AuditLog.objects.filter(ingredient=ing).count(), 3)

    def test_production_is_logged(self):
        r = self.c.post('/api/production/records/', {'recipe_name': 'Cold Brew', 'quantity': 3},
                        format='json')
        self.assertEqual(r.status_code, 201, r.content)
        entry = AuditLog.objects.get(category='production')
        self.assertEqual(entry.production_id, r.json()['id'])
        self.assertEqual(entry.change_label, '3 produced')

    def test_recipe_create_archive_delete_are_logged(self):
        ing = self._ingredient()
        body = {'name': 'Bread', 'category': 'Food', 'price': 50, 'yieldAmount': 1,
                'yieldUnit': 'loaf', 'description': 'd', 'imageUrl': '',
                'ingredients': [{'ingredientId': str(ing.pk), 'quantity': 1, 'unit': 'kg'}]}
        r = self.c.post('/api/recipes/', body, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        rid = r.json()['id']
        self.assertTrue(AuditLog.objects.filter(title='Recipe created', recipe_id=rid).exists())
        self.c.patch(f'/api/recipes/{rid}/', {'isArchived': True}, format='json')
        self.assertTrue(AuditLog.objects.filter(title='Recipe archived').exists())
        self.c.delete(f'/api/recipes/{rid}/')
        self.assertTrue(AuditLog.objects.filter(title='Recipe deleted').exists())

    def test_autoarchive_respects_setting_and_logs(self):
        old = Recipe.objects.create(name='Old', category='food', yield_per_batch=1,
                                    yield_unit='pc', price=1, description='d')
        Recipe.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=45))
        fresh = Recipe.objects.create(name='Fresh', category='food', yield_per_batch=1,
                                      yield_unit='pc', price=1, description='d')
        ProductionRecord.objects.create(recipe_name='Fresh', quantity=1)

        s = Setting.load()
        s.autoarchiveoldrecipe = False
        s.save()
        call_command('autoarchive_recipe')
        old.refresh_from_db()
        self.assertFalse(old.is_archive)

        s.autoarchiveoldrecipe = True
        s.save()
        call_command('autoarchive_recipe')
        old.refresh_from_db(); fresh.refresh_from_db()
        self.assertTrue(old.is_archive)
        self.assertFalse(fresh.is_archive)
        self.assertEqual(AuditLog.objects.filter(title='Recipe archived', recipe=old).count(), 1)
