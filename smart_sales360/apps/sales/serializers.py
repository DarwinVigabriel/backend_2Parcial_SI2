from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.serializers import ProductoSerializer
from apps.products.models import Productos
from decimal import Decimal


class CartItemSerializer(serializers.ModelSerializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Productos.objects.all())
    cart = serializers.PrimaryKeyRelatedField(read_only=True)
    producto_detail = ProductoSerializer(source='producto', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'producto', 'producto_detail', 'quantity', 'price', 'subtotal', 'created_at']
    
    def get_subtotal(self, obj):
        return obj.subtotal


class CartItemCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear items del carrito"""
    class Meta:
        model = CartItem
        fields = ['producto', 'quantity']
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, required=False, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'usuario', 'cliente', 'status', 'total', 'items', 'items_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total', 'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        return obj.items.count()


class VoiceCommandSerializer(serializers.Serializer):
    """Serializer para comandos de voz"""
    audio = serializers.FileField(required=True)
    cart_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate_audio(self, value):
        # Validar que sea un archivo de audio
        allowed_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm']
        file_name = value.name.lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                f"Formato de audio no soportado. Use: {', '.join(allowed_extensions)}"
            )
        
        # Validar tamaño máximo (25MB)
        if value.size > 25 * 1024 * 1024:
            raise serializers.ValidationError("El archivo de audio no debe superar los 25MB")
        
        return value
