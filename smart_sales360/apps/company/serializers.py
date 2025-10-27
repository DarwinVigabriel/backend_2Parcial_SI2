from rest_framework import serializers
from .models import EmpresaConfig


class EmpresaConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaConfig
        fields = '__all__'
