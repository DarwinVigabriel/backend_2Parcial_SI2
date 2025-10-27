from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.serializers import ProductoSerializer
from apps.products.models import Productos


class CartItemSerializer(serializers.ModelSerializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Productos.objects.all())
    cart = serializers.PrimaryKeyRelatedField(read_only=True)
    producto_detail = ProductoSerializer(source='producto', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'producto', 'producto_detail', 'quantity', 'price', 'created_at']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'usuario', 'cliente', 'status', 'total', 'items', 'created_at', 'updated_at']
