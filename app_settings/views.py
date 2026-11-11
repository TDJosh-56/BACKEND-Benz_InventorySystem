from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from audit import services as audit
from .models import Setting
from .serializers import (
    ChangePasscodeSerializer, PasscodeSerializer, RecoveryCodeSerializer,
    ResetPasscodeSerializer, SettingSerializer, # to be implemented (passcode change, reset, recovery)
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
   