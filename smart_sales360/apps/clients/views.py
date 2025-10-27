from rest_framework import viewsets, permissions
from .models import Clientes
from .serializers import ClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Clientes.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
