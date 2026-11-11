from django.test import TestCase
from rest_framework.test import APIClient

from audit.models import AuditLog
from .models import Setting


class SettingsApiTests(TestCase):
    def setUp(self):
        self.c = APIClient()

    def test_get_creates_defaults_and_hides_secrets(self):
        data = self.c.get('/api/settings/').json()
        self.assertTrue(data['autoArchiveOldRecipes'])
        self.assertTrue(data['allowProductionOverride'])
        self.assertNotIn('passcode', str(data).lower())
        self.assertEqual(Setting.objects.count(), 1)

    def test_patch_saves_and_logs_only_real_changes(self):
        r = self.c.patch('/api/settings/', {'autoArchiveOldRecipes': False}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        s = Setting.load()
