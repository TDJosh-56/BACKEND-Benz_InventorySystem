from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from app_settings.models import Setting
from audit.models import AuditLog
from recipe.models import Recipe
from inventory.models import Ingredient
from production.models import Production # (to be implemented)


class AuditHooksTests(TestCase):
    def setUp(self):
        self.c = APIClient()
