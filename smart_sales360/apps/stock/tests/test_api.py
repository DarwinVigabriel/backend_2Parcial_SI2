from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.conf import settings
import jwt
import uuid

from apps.authentication.models import Usuarios
from apps.categories.models import Categorias
from apps.products.models import Productos
from .models import InventarioMovimientos


class StockAPITest(APITestCase):
    def setUp(self):
        self.user = Usuarios.objects.create(id=uuid.uuid4(), email='stock@example.com', password_hash='pbkdf2_sha256$dummy', nombre='S', apellido='U')
        payload = {'user_id': str(self.user.id), 'email': self.user.email}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        self.client = APIClient()
        self.cat = Categorias.objects.create(nombre='StockCat')
        self.prod = Productos.objects.create(sku='STK1', nombre='ProdStock', categoria=self.cat, precio_venta='5.00')

    def test_create_update_delete_movimiento(self):
        url = reverse('inventariomovimientos-list')
        resp = self.client.post(url, {'producto': self.prod.id, 'cantidad': 10, 'stock_anterior': 0, 'stock_nuevo': 10, 'tipo_movimiento': 'in'}, format='json')
        self.assertIn(resp.status_code, (401, 403))

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        resp = self.client.post(url, {'producto': self.prod.id, 'cantidad': 10, 'stock_anterior': 0, 'stock_nuevo': 10, 'tipo_movimiento': 'in'}, format='json')
        self.assertEqual(resp.status_code, 201)
        mid = resp.data.get('id') or resp.data.get('pk')

        detail = reverse('inventariomovimientos-detail', args=[mid])
        resp = self.client.patch(detail, {'motivo': 'ajuste'}, format='json')
        self.assertIn(resp.status_code, (200, 202))

        resp = self.client.delete(detail)
        self.assertIn(resp.status_code, (204, 200))
