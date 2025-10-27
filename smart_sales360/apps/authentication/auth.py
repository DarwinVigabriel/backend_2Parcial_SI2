import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import authentication, exceptions


class SimpleUser:
    """Lightweight user-like object for token auth."""
    def __init__(self, id, email):
        self.id = id
        self.email = email

    @property
    def is_authenticated(self):
        return True


class JWTAuthentication(authentication.BaseAuthentication):
    """Authenticate requests using a simple JWT in Authorization: Bearer <token>"""

    www_authenticate_realm = 'api'

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header or header[0].lower() != b'bearer':
            return None
        if len(header) == 1:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
        if len(header) > 2:
            raise exceptions.AuthenticationFailed('Invalid token header')

        try:
            token = header[1].decode()
        except Exception:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain invalid characters.')

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')

        user_id = payload.get('user_id')
        email = payload.get('email')
        if not user_id:
            raise exceptions.AuthenticationFailed('Invalid payload')

        user = SimpleUser(user_id, email)
        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer realm="%s"' % self.www_authenticate_realm
