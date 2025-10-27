from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import check_password
import jwt
import uuid
from datetime import datetime, timedelta

from .models import Usuarios, UserSessions, DispositivosMoviles, NotificacionPreferencias, Notificaciones
from .serializers import (
    UsuarioSerializer,
    UserSessionSerializer,
    DispositivoSerializer,
    NotificacionPreferenciasSerializer,
    NotificacionSerializer,
    LoginSerializer,
    TokenResponseSerializer,
)


class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Usuarios.objects.all()
    serializer_class = UsuarioSerializer


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserSessions.objects.all()
    serializer_class = UserSessionSerializer


class DispositivoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DispositivosMoviles.objects.all()
    serializer_class = DispositivoSerializer


class NotificacionPreferenciasViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NotificacionPreferencias.objects.all()
    serializer_class = NotificacionPreferenciasSerializer


class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notificaciones.objects.all()
    serializer_class = NotificacionSerializer


class LoginView(APIView):
    """Authenticate a user and return a JWT token.

    This uses the `Usuarios` table and the `password_hash` column. It first
    attempts Django's `check_password` and falls back to strict equality if
    that fails (covers simple legacy hashes). Adjust as needed for your
    project's password hashing scheme.
    """

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = Usuarios.objects.get(email=email)
        except Usuarios.DoesNotExist:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        stored = user.password_hash or ''
        valid = False
        try:
            # Prefer Django's check (handles many hashers)
            valid = check_password(password, stored)
        except Exception:
            valid = False

        # Fallback: direct compare (in case legacy plain text - not recommended)
        if not valid and stored and password == stored:
            valid = True

        if not valid:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Create JWT
        exp_seconds = getattr(settings, 'JWT_EXP_DELTA_SECONDS', 3600)
        exp = datetime.utcnow() + timedelta(seconds=exp_seconds)
        payload = {
            'user_id': str(user.id),
            'email': user.email,
            'exp': exp,
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        # Create a session record (optional) - since models use managed=False this will write to your existing table
        try:
            session = UserSessions(
                id=uuid.uuid4(),
                user=user,
                device_info=request.data.get('device_info'),
                ip_address=request.META.get('REMOTE_ADDR'),
                login_at=timezone.now(),
                expires_at=timezone.now() + timedelta(seconds=exp_seconds),
                is_active=True,
                created_at=timezone.now(),
            )
            session.save()
        except Exception:
            # Don't fail login if session cannot be created; log in future
            pass

        user_data = UsuarioSerializer(user).data
        return Response({'token': token, 'user': user_data}, status=status.HTTP_200_OK)
