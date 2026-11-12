from django.urls import path

from . import views

urlpatterns = [
    path('', views.SettingsView.as_view(), name='settings'),
    path('verify-passcode/', views.VerifyPasscodeView.as_view(), name='settings-verify-passcode'),
    path('verify-recovery/', views.VerifyRecoveryView.as_view(), name='settings-verify-recovery'),
    path('reset-passcode/', views.ResetPasscodeView.as_view(), name='settings-reset-passcode'),
    path('change-passcode/', views.ChangePasscodeView.as_view(), name='settings-change-passcode'),
]