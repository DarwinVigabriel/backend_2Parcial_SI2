from django.db import models


class EmpresaConfig(models.Model):
    nombre_empresa = models.CharField(max_length=255)
    ruc = models.CharField(unique=True, max_length=20)
    direccion_fiscal = models.TextField()
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    logo_url = models.TextField(blank=True, null=True)
    moneda_base = models.CharField(max_length=10, blank=True, null=True)
    iva_percent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    tasa_cambio_usd = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'empresa_config'
