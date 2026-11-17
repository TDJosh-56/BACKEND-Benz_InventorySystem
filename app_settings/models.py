from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

# Same demo credentials the Flutter prototype shipped with.
# Change them right after first run (Settings > Change PIN).
DEFAULT_PASSCODE = '1234'
DEFAULT_RECOVERY_CODE = 'BENZ-9941'

MAX_FAILED_ATTEMPTS = 5
LOCKOUT = timedelta(minutes=5)


class Setting(models.Model):
    """Singleton row (pk=1). Read it with `Setting.load()`."""

    autoarchiveoldrecipe = models.BooleanField(default=True)
    allow_production_override = models.BooleanField(default=True)

    # Credentials are stored hashed, never in plain text.
    passcode_hash = models.CharField(max_length=128, blank = True)
    recovery_code_hash = models.CharField(max_length = 128, blank = True)

    # brute force protection
    failed_attempts = models.PositiveSmallIntegerField(default = 0)
    locked_until = models.DateTimeField(null = True, blank = True)
   
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Setting'
    def __str__(self):
        return 'App Settings'


    # ---- CREDENTIALS (password stuff) -------------------------------------------------

    @classmethod
    def load(cls) -> 'Setting':
        # fetch or create the singleton role (pk = 1) with default demo credentials
        obj, created = cls.objects.get_or_create(pk = 1)
        dirty = False
        if not obj.passcode_hash:
           obj.passcode_hash = make_password(DEFAULT_PASSCODE)
           dirty = True
        if created or dirty:
           obj.save()
        return obj

    def is_locked(self) -> bool:
       # return true if a brute-force lockout window is currently active
       if self.locked_until and timezone.now() < self.locked_until:
          return True 
       if self.locked_until:
          # lockout expired; clear it cleanly
          self.locked_until = None
          self.failed_attempts = 0
          self.save(update_fields = ['locked_until', 'failed_attempts'])
          return False

    def seconds_until_unlock(self) -> int:
       if not self.locked_until:
          return 0
       remaining = (self.locked_until - timezone.now()).total_seconds()
       return max(0, int(remaining))

    def set_passcode(self, raw_passcode: str) -> None:
        self.passcode_hash = make_password(raw_passcode)
        self.failed_attempts = 0
        self.locked_until = None
        self.save(update_fields=['passcode_hash', 'failed_attempts', 'locked_until', 'updated_at'])

    def set_recovery_code(self, raw_code: str) -> None:
        self.recovery_code_hash = make_password(raw_code.strip().upper())
        self.save(update_fields=['recovery_code_hash', 'updated_at'])

    def verify_passcode(self, raw_passcode: str) -> bool:
        #check PIN and update brute-force counters
        if check_password(raw_passcode, self.passcode_hash):
            if self.failed_attempts or self.locked_until:
                self.failed_attempts = 0
                self.locked_until = None
                self.save(update_fields=['failed_attempts', 'locked_until'])
            return True

        self.failed_attempts += 1
        update_fields = ['failed_attempts']
        if self.failed_attempts >= MAX_FAILED_ATTEMPTS:
            self.locked_until = timezone.now() + LOCKOUT
            update_fields.append('locked_until')
        self.save(update_fields=update_fields)
        return False

    def verify_recovery_code(self, raw_code: str) -> bool:
        # check normalized recovery code against stored hash
        normalized = raw_code.strip().upper()
        return check_password(normalized, self.recovery_code_hash)
