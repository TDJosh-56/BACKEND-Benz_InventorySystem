from django.test import TestCase
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from inventory.models import Ingredient
from recipe.models import Recipe, Subcategory

# 1x1 transparent PNG
PNG_B64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
)
TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class RecipeApiTests(APITestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):

        self.milk = Ingredient.objects.create(
            name='Whole Milk', current_stock=10, reorder_threshold=3, unit='L', reorder_unit='L')
        self.sugar = Ingredient.objects.create(
            name='Sugar', current_stock=18, reorder_threshold=8, unit='kg', reorder_unit='kg')
        self.eggs = Ingredient.objects.create(
            name='Eggs', current_stock=10, reorder_threshold=4, unit='Pcs', reorder_unit='Pcs')

        self.list_url = reverse('recipe-list')

    def payload(self, **overrides):
        data = {
            'name': 'Strawberry Frappe',
            'category': 'Drink',
            'subcategory': 'Frappe',
            'price': 120,
            'yieldAmount': 1,
            'yieldUnit': 'cup/batch',
            'description': 'Cold blended drink.',
            'ingredients': [
                {'ingredientId': str(self.milk.pk), 'quantity': 0.25, 'unit': 'L'},
                {'ingredientId': str(self.sugar.pk), 'quantity': 50, 'unit': 'g'},
            ],
        }
        data.update(overrides)
        return data

    # ── create ──

    def test_create_returns_string_ids_and_app_category(self):
        res = self.client.post(self.list_url, self.payload(), format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertIsInstance(res.data['id'], str)
        self.assertEqual(res.data['category'], 'Drink')
        self.assertEqual(Recipe.objects.get().category, 'drinks')  # stored as 'drinks'
        self.assertEqual(res.data['ingredients'][0]['ingredientId'], str(self.milk.pk))
        self.assertEqual(len(res.data['ingredients']), 2)

    def test_create_with_base64_image(self):
        res = self.client.post(
            self.list_url,
            self.payload(imageUrl=f'data:image/png;base64,{PNG_B64}'),
            format='json',
        )
        self.assertEqual(res.status_code, 201, res.data)
        self.assertTrue(res.data['imageUrl'].endswith('.png'))
        self.assertTrue(Recipe.objects.get().image.name.startswith('product/'))

    def test_create_without_image_returns_empty_string(self):
        res = self.client.post(self.list_url, self.payload(), format='json')
        self.assertEqual(res.data['imageUrl'], '')

    def test_invalid_category_rejected(self):
        res = self.client.post(self.list_url, self.payload(category='Dessert'), format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('category', res.data)

    def test_duplicate_ingredient_rejected(self):
        lines = [
            {'ingredientId': str(self.milk.pk), 'quantity': 1, 'unit': 'L'},
            {'ingredientId': str(self.milk.pk), 'quantity': 2, 'unit': 'L'},
        ]
        res = self.client.post(self.list_url, self.payload(ingredients=lines), format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('ingredients', res.data)

    def test_incompatible_unit_rejected(self):
        lines = [{'ingredientId': str(self.eggs.pk), 'quantity': 1, 'unit': 'kg'}]
        res = self.client.post(self.list_url, self.payload(ingredients=lines), format='json')
        self.assertEqual(res.status_code, 400)

    def test_deleted_ingredient_rejected(self):
        self.milk.is_active = False
        self.milk.save()
        lines = [{'ingredientId': str(self.milk.pk), 'quantity': 1, 'unit': 'L'}]
        res = self.client.post(self.list_url, self.payload(ingredients=lines), format='json')
        self.assertEqual(res.status_code, 400)

    def test_non_positive_values_rejected(self):
        for field, value in [('price', 0), ('yieldAmount', 0)]:
            res = self.client.post(self.list_url, self.payload(**{field: value}), format='json')
            self.assertEqual(res.status_code, 400, field)

    def test_subcategory_reused_case_insensitively(self):
        self.client.post(self.list_url, self.payload(name='A', subcategory='Frappe'), format='json')
        self.client.post(self.list_url, self.payload(name='B', subcategory='frappe'), format='json')
        self.assertEqual(Subcategory.objects.count(), 1)

    # ── update ──

    def make_recipe(self, **overrides):
        res = self.client.post(self.list_url, self.payload(**overrides), format='json')
        self.assertEqual(res.status_code, 201, res.data)
        return res.data['id']

    def test_patch_replaces_ingredients(self):
        rid = self.make_recipe()
        url = reverse('recipe-detail', args=[rid])
        res = self.client.patch(url, {
            'ingredients': [{'ingredientId': str(self.eggs.pk), 'quantity': 2, 'unit': 'Pcs'}],
        }, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual([i['ingredientId'] for i in res.data['ingredients']], [str(self.eggs.pk)])

    def test_patch_without_ingredients_keeps_them(self):
        rid = self.make_recipe()
        res = self.client.patch(reverse('recipe-detail', args=[rid]), {'price': 150}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['ingredients']), 2)
        self.assertEqual(res.data['price'], 150)

    def test_patch_existing_image_url_keeps_image(self):
        rid = self.make_recipe(imageUrl=f'data:image/png;base64,{PNG_B64}')
        url = reverse('recipe-detail', args=[rid])
        before = Recipe.objects.get(pk=rid).image.name
        res = self.client.patch(url, {'imageUrl': 'http://testserver/media/' + before}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(Recipe.objects.get(pk=rid).image.name, before)

    def test_patch_empty_image_removes_it(self):
        rid = self.make_recipe(imageUrl=f'data:image/png;base64,{PNG_B64}')
        res = self.client.patch(reverse('recipe-detail', args=[rid]), {'imageUrl': ''}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data['imageUrl'], '')
        self.assertFalse(Recipe.objects.get(pk=rid).image)

    def test_archive_via_patch(self):
        rid = self.make_recipe()
        res = self.client.patch(reverse('recipe-detail', args=[rid]), {'isArchived': True}, format='json')
        self.assertTrue(res.data['isArchived'])

    # ── list / filters / delete ──

    def test_list_filters(self):
        self.make_recipe(name='Latte', category='Drink', subcategory='Hot Coffee')
        self.make_recipe(name='Cake', category='Food', subcategory='Pastries')
        res = self.client.get(self.list_url, {'category': 'Drink'})
        self.assertEqual([r['name'] for r in res.data], ['Latte'])
        res = self.client.get(self.list_url, {'search': 'cake'})
        self.assertEqual([r['name'] for r in res.data], ['Cake'])
        res = self.client.get(self.list_url, {'status': 'archived'})
        self.assertEqual(res.data, [])

    def test_delete(self):
        rid = self.make_recipe()
        res = self.client.delete(reverse('recipe-detail', args=[rid]))
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Recipe.objects.exists())