from django.db import models


class Clientes(models.Model):
    usuario = models.ForeignKey('authentication.Usuarios', models.DO_NOTHING, blank=True, null=True)
    tipo_documento = models.CharField(max_length=10, blank=True, null=True)
    numero_documento = models.CharField(unique=True, max_length=20)
    nombre_completo = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    genero = models.CharField(max_length=1, blank=True, null=True)
    es_empresa = models.BooleanField(blank=True, null=True)
    empresa_nombre = models.CharField(max_length=255, blank=True, null=True)
    puntos_fidelidad = models.IntegerField(blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'clientes'
