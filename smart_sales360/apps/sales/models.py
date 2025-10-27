from django.db import models
import uuid


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey('authentication.Usuarios', models.DO_NOTHING, blank=True, null=True)
    cliente = models.ForeignKey('clients.Clientes', models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=20, default='open')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'carts'


class CartItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    cart = models.ForeignKey('sales.Cart', models.CASCADE, related_name='items')
    producto = models.ForeignKey('products.Productos', models.DO_NOTHING)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'cart_items'

    @property
    def subtotal(self):
        return (self.price or 0) * (self.quantity or 0)
