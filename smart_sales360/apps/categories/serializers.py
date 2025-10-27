from rest_framework import serializers
from .models import Categorias


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorias
        fields = '__all__'

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('El nombre de la categoría no puede estar vacío')
        return value.strip()
