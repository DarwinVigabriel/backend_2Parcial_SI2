from rest_framework import viewsets
from .models import EmpresaConfig
from .serializers import EmpresaConfigSerializer


class EmpresaConfigViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmpresaConfig.objects.all()
    serializer_class = EmpresaConfigSerializer
