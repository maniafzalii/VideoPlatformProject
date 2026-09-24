import uuid
from django.conf import settings


def charge(user, amount):
    if getattr(settings, 'FAKE_GATEWAY_SUCCESS', True):
        return True, uuid.uuid4().hex[:16]
    return False, ''

