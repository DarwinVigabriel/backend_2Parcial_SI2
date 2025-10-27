from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.urls import reverse


class CategoryCRUDTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.list_url = '/api/categories/'

    def test_create_update_delete_category(self):
        # unauthenticated cannot create
        resp = self.client.post(self.list_url, {'nombre': 'Nueva', 'descripcion': 'Desc'})
        self.assertEqual(resp.status_code, 401)

        # authenticate
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.list_url, {'nombre': 'Nueva', 'descripcion': 'Desc'})
        self.assertEqual(resp.status_code, 201)
        obj = resp.json()
        pk = obj.get('id') or obj.get('pk') or obj.get('nombre')

        # update
        detail = f"{self.list_url}{obj.get('id') or obj.get('nombre')}/"
        resp2 = self.client.patch(detail, {'descripcion': 'Modificada'}, format='json')
        self.assertIn(resp2.status_code, (200, 204))

        # delete
        resp3 = self.client.delete(detail)
        self.assertIn(resp3.status_code, (204, 200))
