from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MAX_FAILED_ATTEMPTS, Setting
from .serializers import (
    ChangePasscodeSerializer, 
    PasscodeSerializer, 
    RecoveryCodeSerializer,
    ResetPasscodeSerializer, 
    SettingSerializer, 
)

FIELD_LABELS = {
    'auto_archive_old_recipe': 'Auto archive',
    'allow_production_override': 'Production override',
}


def _locked_response(setting):
    secs = setting.seconds_until_unlock()
    return Response({
        'status': 'locked',
        'message': f'Too many failed attempts. Try again in {max(1, -(-secs // 60))} minute(s).',
        'locked': True,
        'secondsRemaining': secs,
    }, status=status.HTTP_423_LOCKED)


def _failed_response(setting, message):
    """401 for a wrong PIN / recovery code, including lockout info for the UI."""
    locked = setting.is_locked()
    if locked:
        audit.log(AuditLog.Category.SETTINGS, 'Security lockout',
                  f'{MAX_FAILED_ATTEMPTS} failed attempts', 'Locked',
                  AuditLog.Delta.NEGATIVE, setting=setting)
    return Response({
        'status': 'error',
        'message': message,
        'locked': locked,
        'attemptsRemaining': setting.attempts_remaining,
        'secondsRemaining': setting.seconds_until_unlock(),
    }, status=status.HTTP_401_UNAUTHORIZED)


class SettingsView(APIView):
    """
    GET   /api/settings/   -> {autoArchiveOldRecipes, allowProductionOverride, updated_at}
    PATCH /api/settings/   -> same shape; only real changes are written to the audit log
    Credentials are never returned.
    """

    def get(self, request):
        return Response(SettingSerializer(Setting.load()).data)

    @transaction.atomic
    def patch(self, request):
        setting = Setting.load()
        before = {f: getattr(setting, f) for f in FIELD_LABELS}

        ser = SettingSerializer(setting, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        setting = ser.save()

        for field, label in FIELD_LABELS.items():
            old, new = before[field], getattr(setting, field)
            if old == new:
                continue
            audit.log(
                AuditLog.Category.SETTINGS,
                'Setting changed',
                f'{label} turned {"on" if new else "off"}',
                f'{"On" if old else "Off"} → {"On" if new else "Off"}',
                AuditLog.Delta.NEUTRAL,
                setting=setting,
            )
        return Response(SettingSerializer(setting).data)


class VerifyPasscodeView(APIView):
    """POST {recovery_code} -> 200 on success, 401 on a wrong code, 423 while locked."""
    
    @transaction.atomic
    def post(self, request):
        ser = RecoveryCodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
    
        setting = Setting.load()
        if setting.is_locked():
            return _locked_response(setting)
        if setting.verify_recovery_code(ser.validated_data['recovery_code']):
            return Response({'status': 'success', 'message': 'Recovery code verified.'})
        return _failed_response(setting, 'Incorrect recovery code.')


class VerifyRecoveryView(APIView):
    """POST {recovery_code} -> 200 on success, 401 on a wrong code, 423 while locked."""
   
    @transaction.atomic
    def post(self, request):
        ser = RecoveryCodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
   
        setting = Setting.load()
        if setting.is_locked():
            return _locked_response(setting)
        if setting.verify_recovery_code(ser.validated_data['recovery_code']):
            return Response({'status': 'success', 'message': 'Recovery code verified.'})
        return _failed_response(setting, 'Incorrect recovery code.')


class ResetPasscodeView(APIView):
    """POST {recovery_code, new_passcode, confirm_passcode} - forgot-PIN flow."""

    @transaction.atomic
    def post(self, request):
        ser = ResetPasscodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        setting = Setting.load()
        if setting.is_locked():
            return _locked_response(setting)
        if not setting.verify_recovery_code(ser.validated_data['recovery_code']):
            return _failed_response(setting, 'Incorrect recovery code.')

        setting.set_passcode(ser.validated_data['new_passcode'])
        audit.log(AuditLog.Category.SETTINGS, 'Passcode reset', 'Reset with recovery code',
                  'Passcode changed', AuditLog.Delta.NEUTRAL, setting=setting)
        return Response({'status': 'success', 'message': 'Passcode has been reset.'})


class ChangePasscodeView(APIView):
    """POST {current_passcode, new_passcode, confirm_passcode} - Settings > Change PIN."""

    @transaction.atomic
    def post(self, request):
        ser = ChangePasscodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        setting = Setting.load()
        if setting.is_locked():
            return _locked_response(setting)
        if not setting.verify_passcode(ser.validated_data['current_passcode']):
            return _failed_response(setting, 'Current passcode is incorrect.')

        setting.set_passcode(ser.validated_data['new_passcode'])
        audit.log(AuditLog.Category.SETTINGS, 'Passcode changed', 'Security passcode updated',
                  'Passcode changed', AuditLog.Delta.NEUTRAL, setting=setting)
        return Response({'status': 'success', 'message': 'Passcode changed successfully.'})
