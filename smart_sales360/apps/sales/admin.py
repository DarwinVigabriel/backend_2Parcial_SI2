from django.contrib import admin
from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'cliente', 'status', 'total', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('id',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'producto', 'quantity', 'price', 'created_at')
    search_fields = ('producto__nombre',)
