from django.db import models


class Categorias(models.Model):
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    imagen_url = models.TextField(blank=True, null=True)
    color_hex = models.CharField(max_length=7, blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'categorias'
