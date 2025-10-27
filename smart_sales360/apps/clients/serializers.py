from rest_framework import serializers
from .models import Clientes


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clientes
        fields = '__all__'

    def validate_numero_documento(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('El número de documento es obligatorio')
        return value.strip()
