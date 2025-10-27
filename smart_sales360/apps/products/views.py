from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Productos, ProductoPrecioHistorial
from .serializers import ProductoSerializer, ProductoPrecioHistorialSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Productos.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'sku', 'codigo_barras']
    ordering_fields = ['nombre', 'precio_venta', 'stock_actual']

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def lookup_by_barcode(self, request):
        barcode = request.query_params.get('barcode')
        if not barcode:
            return Response({'detail': 'barcode param required'}, status=400)
        try:
            p = Productos.objects.get(codigo_barras=barcode)
        except Productos.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=404)
        return Response(ProductoSerializer(p).data)


class ProductoPrecioHistorialViewSet(viewsets.ModelViewSet):
    queryset = ProductoPrecioHistorial.objects.all()
    serializer_class = ProductoPrecioHistorialSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
