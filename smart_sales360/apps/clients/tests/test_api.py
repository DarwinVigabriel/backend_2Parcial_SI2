from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.conf import settings
import jwt
import uuid

from apps.authentication.models import Usuarios
from .models import Clientes


class ClienteAPITest(APITestCase):
    def setUp(self):
        self.user = Usuarios.objects.create(id=uuid.uuid4(), email='client@example.com', password_hash='pbkdf2_sha256$dummy', nombre='C', apellido='U')
        payload = {'user_id': str(self.user.id), 'email': self.user.email}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        self.client = APIClient()

    def test_create_update_delete_cliente(self):
        url = reverse('clientes-list')
        resp = self.client.post(url, {'numero_documento': '12345', 'nombre_completo': 'Cliente Test'}, format='json')
        self.assertIn(resp.status_code, (401, 403))

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        resp = self.client.post(url, {'numero_documento': '12345', 'nombre_completo': 'Cliente Test'}, format='json')
        self.assertEqual(resp.status_code, 201)
        cid = resp.data.get('id') or resp.data.get('pk')

        detail = reverse('clientes-detail', args=[cid])
        resp = self.client.patch(detail, {'telefono': '999'}, format='json')
        self.assertIn(resp.status_code, (200, 202))

        resp = self.client.delete(detail)
        self.assertIn(resp.status_code, (204, 200))
