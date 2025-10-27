from rest_framework import viewsets, permissions
from .models import Productos, ProductoPrecioHistorial
from .serializers import ProductoSerializer, ProductoPrecioHistorialSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Productos.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProductoPrecioHistorialViewSet(viewsets.ModelViewSet):
    queryset = ProductoPrecioHistorial.objects.all()
    serializer_class = ProductoPrecioHistorialSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
