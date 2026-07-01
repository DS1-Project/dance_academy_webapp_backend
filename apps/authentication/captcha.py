import json
import urllib.parse
import urllib.request

from django.conf import settings
from rest_framework import serializers


def verify_captcha(token: str) -> bool:
    if not token:
        return False

    if settings.DEBUG and token == 'dev-bypass':
        return True

    secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
    if not secret_key:
        return settings.DEBUG

    payload = urllib.parse.urlencode(
        {'secret': secret_key, 'response': token}
    ).encode()
    request = urllib.request.Request(
        'https://www.google.com/recaptcha/api/siteverify',
        data=payload,
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode())
            return result.get('success', False)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return False


def validate_captcha_token(token: str) -> None:
    if not verify_captcha(token):
        raise serializers.ValidationError('CAPTCHA inválido o expirado.')
