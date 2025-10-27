from django.contrib import admin
from .models import EmpresaConfig


@admin.register(EmpresaConfig)
class EmpresaConfigAdmin(admin.ModelAdmin):
    list_display = ('nombre_empresa', 'ruc', 'email')
    search_fields = ('nombre_empresa', 'ruc')
