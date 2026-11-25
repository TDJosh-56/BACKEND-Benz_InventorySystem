from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from audit.models import AuditLog
from .models import DEFAULT_PASSCODE, DEFAULT_RECOVERY_CODE, MAX_FAILED_ATTEMPTS, Setting

URL = '/api/settings/'


class SettingsApiTests(TestCase):
    def setUp(self):
        self.c = APIClient()
        
    def post(self, path, body):
        return self.c.post(URL + path, body, format='json')

    def test_get_creates_defaults_and_hides_secrets(self):
        data = self.c.get(URL).json()
        self.assertTrue(data['autoArchiveOldRecipes'])
        self.assertTrue(data['allowProductionOverride'])
        self.assertNotIn('passcode', str(data).lower())
        self.assertNotIn('hash', str(data).lower())
        self.assertEqual(Setting.objects.count(), 1)

    def test_patch_saves_and_logs_only_real_changes(self):
        r = self.c.patch('/api/settings/', {'autoArchiveOldRecipes': False}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertFalse(Setting.load().autoarchiveoldrecipe)
        e = AuditLog.objects.get()
        self.assertEqual((e.category, e.title, e.subtitle, e.change_label),
                         ('settings', 'Setting changed', 'Auto archive old recipes turned off', 'On → Off'))
        self.assertIsNotNone(e.settings_id)

        
        self.c.patch(URL, {'autoArchiveOldRecipes': False}, format='json')
        self.assertEqual(AuditLog.objects.count(), 1)

        # The removed production-override preference is no longer accepted or exposed.
        removed = self.c.patch(URL, {'allowProductionOverride': False}, format='json')
        self.assertEqual(removed.status_code, 200)
        self.assertNotIn('allowProductionOverride', removed.json())       
        self.assertEqual(AuditLog.objects.count(), 1)
        
        
    def test_auto_archive_patch_is_persisted_and_returned(self):
        response = self.c.patch(URL, {'autoArchiveOldRecipes': False}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(response.json()['autoArchiveOldRecipes'])
        self.assertFalse(Setting.load().autoarchiveoldrecipe)
        
        # A fresh GET (as Django Admin reads the same model row) sees the same value.
        fresh = self.c.get(URL)
        self.assertEqual(fresh.status_code, 200)
        self.assertFalse(fresh.json()['autoArchiveOldRecipes'])

    def test_removed_production_override_is_not_a_model_field(self):
        self.assertNotIn(
            'allow_production_override',
            {field.name for field in Setting._meta.get_fields()},
        )


    def test_django_admin_no_longer_displays_removed_override(self):
        from .admin import SettingAdmin

        self.assertNotIn('allow_production_override', SettingAdmin.list_display)
        self.assertIn('autoarchiveoldrecipe', SettingAdmin.list_display)
        self.assertIn('autoarchiveoldrecipe', SettingAdmin.list_editable)

    def test_patch_rejects_non_boolean(self):
        self.assertEqual(self.c.patch(URL, {'autoArchiveOldRecipes': 'maybe'}, format='json').status_code, 400)

    # ---- passcode ------------------------------------------------------
    def test_verify_passcode(self):
        self.assertEqual(self.post('verify-passcode/', {'passcode': DEFAULT_PASSCODE}).status_code, 200)
        bad = self.post('verify-passcode/', {'passcode': '0000'})
        self.assertEqual(bad.status_code, 401)
        self.assertEqual(bad.json()['attemptsRemaining'], MAX_FAILED_ATTEMPTS - 1)
        self.assertEqual(self.post('verify-passcode/', {'passcode': 'abcd'}).status_code, 400)

    def test_lockout_after_too_many_failures_then_expires(self):
        for _ in range(MAX_FAILED_ATTEMPTS):
            r = self.post('verify-passcode/', {'passcode': '0000'})
        self.assertTrue(r.json()['locked'])
        self.assertEqual(AuditLog.objects.filter(title='Security lockout').count(), 1)

        # even the right PIN is refused while locked
        r = self.post('verify-passcode/', {'passcode': DEFAULT_PASSCODE})
        self.assertEqual(r.status_code, 423)
        self.assertGreater(r.json()['secondsRemaining'], 0)

        Setting.objects.update(locked_until=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.post('verify-passcode/', {'passcode': DEFAULT_PASSCODE}).status_code, 200)
        self.assertEqual(Setting.load().failed_attempts, 0)

    def test_change_passcode(self):
        body = {'current_passcode': '1234', 'new_passcode': '4321', 'confirm_passcode': '4321'}
        self.assertEqual(self.post('change-passcode/', {**body, 'current_passcode': '9999'}).status_code, 401)
        self.assertEqual(self.post('change-passcode/', {**body, 'confirm_passcode': '1111'}).status_code, 400)
        self.assertEqual(self.post('change-passcode/', {**body, 'new_passcode': '1234',
                                                        'confirm_passcode': '1234'}).status_code, 400)
        self.assertEqual(self.post('change-passcode/', {**body, 'new_passcode': '12ab',
                                                        'confirm_passcode': '12ab'}).status_code, 400)
        self.assertEqual(self.post('change-passcode/', body).status_code, 200)

        self.assertEqual(self.post('verify-passcode/', {'passcode': '4321'}).status_code, 200)
        self.assertEqual(self.post('verify-passcode/', {'passcode': '1234'}).status_code, 401)
        entry = AuditLog.objects.get(title='Passcode changed')
        self.assertNotIn('4321', f'{entry.subtitle}{entry.change_label}')

    # ---- recovery ------------------------------------------------------
    def test_verify_recovery_is_case_insensitive(self):
        self.assertEqual(self.post('verify-recovery/', {'recovery_code': ' benz-9941 '}).status_code, 200)
        self.assertEqual(self.post('verify-recovery/', {'recovery_code': 'NOPE'}).status_code, 401)

    def test_reset_passcode_with_recovery_code(self):
        body = {'recovery_code': DEFAULT_RECOVERY_CODE, 'new_passcode': '5555', 'confirm_passcode': '5555'}
        self.assertEqual(self.post('reset-passcode/', {**body, 'recovery_code': 'WRONG'}).status_code, 401)
        self.assertEqual(self.post('reset-passcode/', {**body, 'confirm_passcode': '1111'}).status_code, 400)
        self.assertEqual(self.post('reset-passcode/', body).status_code, 200)
        self.assertEqual(self.post('verify-passcode/', {'passcode': '5555'}).status_code, 200)
        self.assertTrue(AuditLog.objects.filter(title='Passcode reset').exists())

    def test_reset_is_blocked_while_locked(self):
        for _ in range(MAX_FAILED_ATTEMPTS):
            self.post('verify-passcode/', {'passcode': '0000'})
        # locked -> reset is blocked too (recovery code cannot be brute-forced around the lock)
        body = {'recovery_code': DEFAULT_RECOVERY_CODE, 'new_passcode': '5555', 'confirm_passcode': '5555'}
        self.assertEqual(self.post('reset-passcode/', body).status_code, 423)