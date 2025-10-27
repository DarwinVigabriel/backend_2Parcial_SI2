from django.contrib import admin
from .models import Productos, ProductoPrecioHistorial


@admin.register(Productos)
class ProductosAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'categoria', 'precio_venta', 'activo')
    search_fields = ('sku', 'nombre')


@admin.register(ProductoPrecioHistorial)
class ProductoPrecioHistorialAdmin(admin.ModelAdmin):
    list_display = ('producto', 'precio_nuevo', 'created_at')
