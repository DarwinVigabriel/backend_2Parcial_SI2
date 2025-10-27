from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.conf import settings
import jwt
import uuid

from apps.authentication.models import Usuarios
from apps.categories.models import Categorias
from .models import Productos


class ProductoAPITest(APITestCase):
    def setUp(self):
        self.user = Usuarios.objects.create(id=uuid.uuid4(), email='product@example.com', password_hash='pbkdf2_sha256$dummy', nombre='P', apellido='U')
        payload = {'user_id': str(self.user.id), 'email': self.user.email}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        self.client = APIClient()
        # create a category
        self.cat = Categorias.objects.create(nombre='CatTest')

    def test_create_update_delete_producto(self):
        url = reverse('products-list')
        # unauthenticated create
        resp = self.client.post(url, {'sku': 'SKU1', 'nombre': 'P1', 'categoria': self.cat.id, 'precio_venta': '10.00'}, format='json')
        self.assertIn(resp.status_code, (401, 403))

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        resp = self.client.post(url, {'sku': 'SKU1', 'nombre': 'P1', 'categoria': self.cat.id, 'precio_venta': '10.00'}, format='json')
        self.assertEqual(resp.status_code, 201)
        prod_id = resp.data.get('id') or resp.data.get('pk')

        detail = reverse('products-detail', args=[prod_id])
        resp = self.client.patch(detail, {'precio_venta': '12.50'}, format='json')
        self.assertIn(resp.status_code, (200, 202))

        resp = self.client.delete(detail)
        self.assertIn(resp.status_code, (204, 200))
