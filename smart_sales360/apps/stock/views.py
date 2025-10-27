from rest_framework import viewsets, permissions
from .models import InventarioMovimientos
from .serializers import InventarioMovimientosSerializer


class InventarioMovimientosViewSet(viewsets.ModelViewSet):
    queryset = InventarioMovimientos.objects.all()
    serializer_class = InventarioMovimientosSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
