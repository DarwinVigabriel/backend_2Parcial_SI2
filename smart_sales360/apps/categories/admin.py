from django.contrib import admin
from .models import Categorias


@admin.register(Categorias)
class CategoriasAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    search_fields = ('nombre',)
