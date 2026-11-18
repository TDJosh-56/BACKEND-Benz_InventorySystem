from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from app_settings.models import Setting
from audit.models import AuditLog
from recipe.models import Recipe
from inventory.models import Ingredient


class AuditApiTests(TestCase):
    def setUp(self):
        self.c = APIClient()

    def _make(self, **kw):
        kw.setdefault('category', 'recipe')
        kw.setdefault('title', 'T')
        return AuditLog.objects.create(**kw)

    def test_list_shape_and_order(self):
        a = self._make(title='old', timestamp=timezone.now() - timedelta(days=2))
        b = self._make(title='new', change_label='5 -> 6 kg', delta_type='positive')
        rows = self.c.get('/api/audit-logs/').json()
        self.assertEqual([r['title'] for r in rows], ['new', 'old'])
        self.assertEqual(rows[0]['id'], f'LOG-{b.pk:06d}')
        self.assertEqual(rows[0]['badgeText'], 'RECIPE')
        self.assertEqual(rows[0]['changeLabel'], '5 -> 6 kg')
        self.assertEqual(rows[0]['deltaType'], 'positive')
        self.assertIsNone(rows[0]['recipeId'])

    def test_filters(self):
        self._make(category='inventory', title='Flour')
        self._make(category='settings', title='Auto archive enabled')
        self._make(category='recipe', title='Old', timestamp=timezone.now() - timedelta(days=60))
        self.assertEqual(len(self.c.get('/api/audit-logs/?category=inventory').json()), 1)
        self.assertEqual(len(self.c.get('/api/audit-logs/?search=archive').json()), 1)
        self.assertEqual(len(self.c.get('/api/audit-logs/?period=day').json()), 2)
        self.assertEqual(self.c.get('/api/audit-logs/?category=bogus').status_code, 400)
        self.assertEqual(self.c.get('/api/audit-logs/?period=year').status_code, 400)
        self.assertEqual(self.c.get('/api/audit-logs/?period=day&date=nope').status_code, 400)

    def test_post_creates_entry_and_server_stamps_time(self):
        r = self.c.post('/api/audit-logs/', {
            'category': 'production', 'title': 'Batch', 'timestamp': '2000-01-01T00:00:00Z'},
            format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertGreater(AuditLog.objects.get().timestamp.year, 2000)

    def test_append_only(self):
        e = self._make()
        self.assertEqual(self.c.patch(f'/api/audit-logs/{e.pk}/', {}, format='json').status_code, 404)
        self.assertEqual(self.c.delete('/api/audit-logs/').status_code, 405)


class AuditHooksTests(TestCase):
    def setUp(self):
        self.c = APIClient()
        
    def _ingredient(self, **kw):
        body = {'ingredient': 'Flour', 'stock': 10, 'unit': 'kg', 'threshold': 2}
        body.update(kw)
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
