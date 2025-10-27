from django.contrib import admin
from .models import Clientes


@admin.register(Clientes)
class ClientesAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'numero_documento', 'email', 'telefono')
    search_fields = ('nombre_completo', 'numero_documento', 'email')
