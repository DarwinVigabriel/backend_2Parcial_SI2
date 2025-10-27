from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User


class ProductsCRUDTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='produser', password='pass')
        self.list_url = '/api/products/products/'

    def test_create_update_delete_product(self):
        # unauthenticated cannot create
        resp = self.client.post(self.list_url, {'sku': 'SKU123', 'nombre': 'Prod 1', 'precio_venta': '10.00'})
        self.assertEqual(resp.status_code, 401)

        self.client.force_authenticate(user=self.user)
        # need to provide category FK; try to create a category first
        cat_resp = self.client.post('/api/categories/', {'nombre': 'CatX'})
        self.assertEqual(cat_resp.status_code, 201)
        categoria = cat_resp.json()
        categoria_key = categoria.get('id') or categoria.get('nombre')

        resp = self.client.post(self.list_url, {'sku': 'SKU123', 'nombre': 'Prod 1', 'precio_venta': '10.00', 'categoria': categoria_key})
        self.assertEqual(resp.status_code, 201)
        prod = resp.json()
        prod_id = prod.get('id') or prod.get('sku')

        detail = f"/api/products/products/{prod.get('id') or prod.get('sku')}/"
        resp2 = self.client.patch(detail, {'precio_venta': '12.50'}, format='json')
        self.assertIn(resp2.status_code, (200, 204))

        resp3 = self.client.delete(detail)
        self.assertIn(resp3.status_code, (204, 200))
