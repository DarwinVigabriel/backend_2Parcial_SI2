from django.db import models


class Productos(models.Model):
    sku = models.CharField(unique=True, max_length=100)
    codigo_barras = models.CharField(unique=True, max_length=100, blank=True, null=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    # reference to Categorias in categories app
    categoria = models.ForeignKey('categories.Categorias', models.DO_NOTHING)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2)
    precio_compra = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    stock_actual = models.IntegerField(blank=True, null=True)
    stock_minimo = models.IntegerField(blank=True, null=True)
    stock_maximo = models.IntegerField(blank=True, null=True)
    peso_kg = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    dimensiones = models.JSONField(blank=True, null=True)
    imagen_url = models.TextField(blank=True, null=True)
    etiquetas = models.TextField(blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'productos'


class ProductoPrecioHistorial(models.Model):
    producto = models.ForeignKey('products.Productos', models.DO_NOTHING)
    precio_anterior = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    precio_nuevo = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.CharField(max_length=100, blank=True, null=True)
    usuario = models.ForeignKey('authentication.Usuarios', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'producto_precio_historial'
