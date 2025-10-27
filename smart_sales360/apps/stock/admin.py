from django.contrib import admin
from .models import InventarioMovimientos


@admin.register(InventarioMovimientos)
class InventarioMovimientosAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo_movimiento', 'cantidad', 'created_at')
    search_fields = ('producto__nombre', 'producto__sku')
