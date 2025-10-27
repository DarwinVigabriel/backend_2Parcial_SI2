from rest_framework import serializers
from .models import Usuarios, UserSessions, DispositivosMoviles, NotificacionPreferencias, Notificaciones


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = '__all__'


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSessions
        fields = '__all__'


class DispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispositivosMoviles
        fields = '__all__'


class NotificacionPreferenciasSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificacionPreferencias
        fields = '__all__'


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificaciones
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    user = UsuarioSerializer()
