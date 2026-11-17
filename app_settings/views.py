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





class SettingsView(APIView):
 


class VerifyPasscodeView(APIView):



class VerifyRecoveryView(APIView):
   


class ResetPasscodeView(APIView):
  


class ChangePasscodeView(APIView):
   