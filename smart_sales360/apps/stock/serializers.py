from rest_framework import serializers
from .models import InventarioMovimientos


class InventarioMovimientosSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventarioMovimientos
        fields = '__all__'

    def validate_cantidad(self, value):
        if value == 0:
            raise serializers.ValidationError('La cantidad no puede ser cero')
        return value
