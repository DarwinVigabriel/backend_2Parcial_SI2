from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User


class SalesCRUDTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='salesuser', password='pass')
        # create a category
        self.client.force_authenticate(user=self.user)
        cat_resp = self.client.post('/api/categories/', {'nombre': 'CartCat'})
        self.assertEqual(cat_resp.status_code, 201)
        categoria = cat_resp.json()
        categoria_key = categoria.get('id') or categoria.get('nombre')
        # create a product with barcode
        prod_resp = self.client.post('/api/products/products/', {'sku': 'SKU-C1', 'nombre': 'CartProd', 'precio_venta': '5.00', 'categoria': categoria_key, 'codigo_barras': '1234567890'})
        self.assertEqual(prod_resp.status_code, 201)
        self.product = prod_resp.json()

    def test_cart_create_additem_checkout_and_barcode_lookup(self):
        # create cart
        self.client.force_authenticate(user=self.user)
        cart_resp = self.client.post('/api/sales/carts/', {})
        self.assertEqual(cart_resp.status_code, 201)
        cart = cart_resp.json()
        cart_id = cart.get('id')

        # add item
        add_resp = self.client.post(f'/api/sales/carts/{cart_id}/add_item/', {'producto': self.product.get('id') or self.product.get('sku'), 'quantity': 2, 'price': '5.00'})
        self.assertEqual(add_resp.status_code, 201)
        # lookup barcode
        lookup = self.client.get('/api/products/products/lookup_by_barcode/', {'barcode': '1234567890'})
        self.assertEqual(lookup.status_code, 200)

        # checkout
        checkout = self.client.post(f'/api/sales/carts/{cart_id}/checkout/')
        self.assertEqual(checkout.status_code, 200)
