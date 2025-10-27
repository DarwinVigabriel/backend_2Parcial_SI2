from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User


class ClientsCRUDTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='cliuser', password='pass')
        self.list_url = '/api/clients/'

    def test_create_update_delete_client(self):
        resp = self.client.post(self.list_url, {'numero_documento': '12345', 'nombre_completo': 'Cliente Uno'})
        self.assertEqual(resp.status_code, 401)

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.list_url, {'numero_documento': '12345', 'nombre_completo': 'Cliente Uno'})
        self.assertEqual(resp.status_code, 201)
        obj = resp.json()
        identifier = obj.get('id') or obj.get('numero_documento')

        detail = f"{self.list_url}{identifier}/"
        resp2 = self.client.patch(detail, {'telefono': '9999999'}, format='json')
        self.assertIn(resp2.status_code, (200, 204))

        resp3 = self.client.delete(detail)
        self.assertIn(resp3.status_code, (204, 200))
