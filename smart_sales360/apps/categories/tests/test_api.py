from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.conf import settings
import jwt
import uuid

from apps.authentication.models import Usuarios
from .models import Categorias


class CategoriaAPITest(APITestCase):
    def setUp(self):
        # create a test user in Usuarios
        self.user = Usuarios.objects.create(id=uuid.uuid4(), email='test@example.com', password_hash='pbkdf2_sha256$dummy', nombre='Test', apellido='User')
        payload = {'user_id': str(self.user.id), 'email': self.user.email}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        self.client = APIClient()

    def test_create_update_delete_categoria(self):
        url = reverse('categorias-list')
        # unauthenticated create should be forbidden (403)
        resp = self.client.post(url, {'nombre': 'Nueva'}, format='json')
        self.assertIn(resp.status_code, (401, 403))

        # authenticate
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        resp = self.client.post(url, {'nombre': 'Nueva', 'descripcion': 'desc'}, format='json')
        self.assertEqual(resp.status_code, 201)
        cat_id = resp.data.get('id') or resp.data.get('pk')

        # update
        detail = reverse('categorias-detail', args=[cat_id])
        resp = self.client.patch(detail, {'descripcion': 'updated'}, format='json')
        self.assertIn(resp.status_code, (200, 202))

        # delete
        resp = self.client.delete(detail)
        self.assertIn(resp.status_code, (204, 200))
