from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

# Same demo credentials the Flutter prototype shipped with.# Change them right after first run (Settings > Change PIN).
DEFAULT_PASSCODE = '1234'
DEFAULT_RECOVERY_CODE = 'BENZ-9941'

MAX_FAILED_ATTEMPTS = 5
LOCKOUT = timedelta(minutes=5)


class Setting(models.Model):
    """Singleton row (pk=1). Read it with `Setting.load()`."""

    autoarchiveoldrecipe = models.BooleanField(default=True)
    allow_production_override = models.BooleanField(default=True)

    # Credentials are stored hashed, never in plain text.
   
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Setting'


    # ---- CREDENTIALS (password stuff) -------------------------------------------------
