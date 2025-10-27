from rest_framework import serializers
from .models import Productos, ProductoPrecioHistorial


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Productos
        fields = '__all__'

    def validate_precio_venta(self, value):
        if value is None or value < 0:
            raise serializers.ValidationError('El precio de venta debe ser un número >= 0')
        return value

    def validate_stock_actual(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('El stock no puede ser negativo')
        return value


class ProductoPrecioHistorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoPrecioHistorial
        fields = '__all__'
