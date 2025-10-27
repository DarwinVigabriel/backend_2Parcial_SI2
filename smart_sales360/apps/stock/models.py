from django.db import models


class InventarioMovimientos(models.Model):
    producto = models.ForeignKey('products.Productos', models.DO_NOTHING)
    tipo_movimiento = models.CharField(max_length=20, blank=True, null=True)
    cantidad = models.IntegerField()
    stock_anterior = models.IntegerField()
    stock_nuevo = models.IntegerField()
    motivo = models.CharField(max_length=100, blank=True, null=True)
    referencia_id = models.IntegerField(blank=True, null=True)
    referencia_tipo = models.CharField(max_length=50, blank=True, null=True)
    usuario = models.ForeignKey('authentication.Usuarios', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'inventario_movimientos'
