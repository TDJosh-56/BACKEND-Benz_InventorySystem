from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import AnonRateThrottle


class LoginThrottle(AnonRateThrottle):
    rate = '5/minute'   # slows down password guessing


class LoginView(ObtainAuthToken):
    throttle_classes = [LoginThrottle]