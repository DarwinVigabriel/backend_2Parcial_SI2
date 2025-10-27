from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User


class StockCRUDTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='stockuser', password='pass')
        self.list_url = '/api/stock/'

    def test_create_update_delete_move(self):
        resp = self.client.post(self.list_url, {'producto': 1, 'cantidad': 5, 'stock_anterior': 0, 'stock_nuevo': 5})
        self.assertEqual(resp.status_code, 401)

        self.client.force_authenticate(user=self.user)
        # Create a category + product dependency
        cat_resp = self.client.post('/api/categories/', {'nombre': 'StockCat'})
        self.assertEqual(cat_resp.status_code, 201)
        cat = cat_resp.json()
        cat_key = cat.get('id') or cat.get('nombre')

        prod_resp = self.client.post('/api/products/products/', {'sku': 'STK1', 'nombre': 'P', 'precio_venta': '1.00', 'categoria': cat_key})
        self.assertEqual(prod_resp.status_code, 201)
        prod = prod_resp.json()
        prod_key = prod.get('id') or prod.get('sku')

        resp = self.client.post(self.list_url, {'producto': prod_key, 'cantidad': 5, 'stock_anterior': 0, 'stock_nuevo': 5})
        self.assertEqual(resp.status_code, 201)
        obj = resp.json()
        identifier = obj.get('id') or obj.get('pk')

        detail = f"{self.list_url}{identifier}/"
        resp2 = self.client.patch(detail, {'motivo': 'Ajuste'}, format='json')
        self.assertIn(resp2.status_code, (200, 204))

        resp3 = self.client.delete(detail)
        self.assertIn(resp3.status_code, (204, 200))
