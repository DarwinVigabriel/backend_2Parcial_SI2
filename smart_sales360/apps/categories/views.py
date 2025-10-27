from rest_framework import viewsets, permissions
from .models import Categorias
from .serializers import CategoriaSerializer


class CategoriaViewSet(viewsets.ModelViewSet):
    """Full CRUD for categories. Read permission is open; writes require authentication."""
    queryset = Categorias.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
