"""
CU16: Dashboard de Ventas Históricas
Módulo para calcular estadísticas y generar reportes de ventas
"""

from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta
from .models import Venta, VentaDetalle
from decimal import Decimal


class EstadisticasVentas:
    """
    Clase para calcular estadísticas y métricas de ventas
    Soporta filtrados por período, cliente, estado, etc.
    """
    
    def __init__(self, fecha_inicio=None, fecha_fin=None, cliente_id=None, estado=None):
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.cliente_id = cliente_id
        self.estado = estado
        self.queryset = self._get_filtered_queryset()
    
    def _get_filtered_queryset(self):
        """Obtiene queryset filtrado según los parámetros"""
        qs = Venta.objects.all()
        
        if self.fecha_inicio:
            qs = qs.filter(fecha_venta__gte=self.fecha_inicio)
        
        if self.fecha_fin:
            qs = qs.filter(fecha_venta__lte=self.fecha_fin)
        
        if self.cliente_id:
            qs = qs.filter(cliente_id=self.cliente_id)
        
        if self.estado:
            qs = qs.filter(estado=self.estado)
        
        return qs
    
    def obtener_estadisticas_completas(self):
        """Retorna un diccionario con todas las estadísticas"""
        return {
            'resumen': self.obtener_resumen(),
            'por_estado': self.obtener_ventas_por_estado(),
            'por_metodo_pago': self.obtener_ventas_por_metodo(),
            'top_productos': self.obtener_top_productos(),
            'vendedores': self.obtener_ventas_por_vendedor(),
        }
    
    def obtener_resumen(self):
        """Obtiene resumen general de ventas"""
        stats = self.queryset.aggregate(
            total_vendido=Sum('total'),
            cantidad_ventas=Count('id'),
            promedio_por_venta=Avg('total'),
            total_descuentos=Sum('descuento'),
            total_impuestos=Sum('iva'),
            subtotal=Sum('subtotal')
        )
        
        return {
            'total_vendido': stats['total_vendido'] or Decimal('0'),
            'cantidad_ventas': stats['cantidad_ventas'] or 0,
            'promedio_por_venta': stats['promedio_por_venta'] or Decimal('0'),
            'total_descuentos': stats['total_descuentos'] or Decimal('0'),
            'total_impuestos': stats['total_impuestos'] or Decimal('0'),
            'subtotal': stats['subtotal'] or Decimal('0'),
        }
    
    def obtener_ventas_por_estado(self):
        """Obtiene cantidad de ventas por estado"""
        return {
            'pendiente': self.queryset.filter(estado='pendiente').count(),
            'pagada': self.queryset.filter(estado='pagada').count(),
            'cancelada': self.queryset.filter(estado='cancelada').count(),
            'reembolsada': self.queryset.filter(estado='reembolsada').count(),
            'en_proceso': self.queryset.filter(estado='en_proceso').count(),
        }
    
    def obtener_ventas_por_metodo(self):
        """Obtiene cantidad y monto de ventas por método de pago"""
        return {
            'tarjeta': {
                'cantidad': self.queryset.filter(metodo_pago='tarjeta').count(),
                'monto': self.queryset.filter(metodo_pago='tarjeta').aggregate(Sum('total'))['total__sum'] or Decimal('0'),
            },
            'efectivo': {
                'cantidad': self.queryset.filter(metodo_pago='efectivo').count(),
                'monto': self.queryset.filter(metodo_pago='efectivo').aggregate(Sum('total'))['total__sum'] or Decimal('0'),
            },
            'transferencia': {
                'cantidad': self.queryset.filter(metodo_pago='transferencia').count(),
                'monto': self.queryset.filter(metodo_pago='transferencia').aggregate(Sum('total'))['total__sum'] or Decimal('0'),
            },
            'paypal': {
                'cantidad': self.queryset.filter(metodo_pago='paypal').count(),
                'monto': self.queryset.filter(metodo_pago='paypal').aggregate(Sum('total'))['total__sum'] or Decimal('0'),
            },
            'stripe': {
                'cantidad': self.queryset.filter(metodo_pago='stripe').count(),
                'monto': self.queryset.filter(metodo_pago='stripe').aggregate(Sum('total'))['total__sum'] or Decimal('0'),
            },
        }
    
    def obtener_top_productos(self, limite=10):
        """Obtiene los productos más vendidos"""
        top = VentaDetalle.objects.filter(
            venta__in=self.queryset
        ).values(
            'producto__nombre',
            'producto__sku'
        ).annotate(
            cantidad_total=Sum('cantidad'),
            monto_total=Sum('subtotal')
        ).order_by('-cantidad_total')[:limite]
        
        return [
            {
                'nombre': item['producto__nombre'],
                'sku': item['producto__sku'],
                'cantidad': item['cantidad_total'],
                'monto': item['monto_total'],
            }
            for item in top
        ]
    
    def obtener_ventas_por_vendedor(self):
        """Obtiene estadísticas por vendedor"""
        from django.db.models import F, FloatField
        from django.db.models.functions import Cast
        
        vendedores = self.queryset.values(
            'usuario__nombre'
        ).annotate(
            cantidad=Count('id'),
            total=Sum('total')
        ).order_by('-total')
        
        # Calcular promedio manualmente
        resultado = []
        for item in vendedores:
            promedio = item['total'] / item['cantidad'] if item['cantidad'] > 0 else 0
            resultado.append({
                'vendedor': item['usuario__nombre'],
                'cantidad': item['cantidad'],
                'total': item['total'],
                'promedio': promedio,
            })
        
        return resultado
    
    def obtener_tendencia_diaria(self, dias=30):
        """Obtiene tendencia de ventas por día en los últimos N días"""
        ahora = timezone.now()
        hace_n_dias = ahora - timedelta(days=dias)
        
        tendencia = self.queryset.filter(
            fecha_venta__gte=hace_n_dias
        ).extra(
            select={'fecha': 'DATE(fecha_venta)'}
        ).values('fecha').annotate(
            cantidad=Count('id'),
            total=Sum('total')
        ).order_by('fecha')
        
        return [
            {
                'fecha': item['fecha'].isoformat(),
                'cantidad': item['cantidad'],
                'total': float(item['total']),
            }
            for item in tendencia
        ]
    
    def obtener_tendencia_mensual(self, meses=12):
        """Obtiene tendencia de ventas por mes en los últimos N meses"""
        ahora = timezone.now()
        hace_n_meses = ahora - timedelta(days=30*meses)
        
        tendencia = self.queryset.filter(
            fecha_venta__gte=hace_n_meses
        ).extra(
            select={'mes': 'DATE_TRUNC(\'month\', fecha_venta)'}
        ).values('mes').annotate(
            cantidad=Count('id'),
            total=Sum('total')
        ).order_by('mes')
        
        return [
            {
                'mes': item['mes'].isoformat() if item['mes'] else None,
                'cantidad': item['cantidad'],
                'total': float(item['total']),
            }
            for item in tendencia
        ]


def calcular_estadisticas_ventas(fecha_inicio=None, fecha_fin=None, cliente_id=None, estado=None):
    """
    Función helper para calcular estadísticas
    
    Args:
        fecha_inicio: datetime (opcional)
        fecha_fin: datetime (opcional)
        cliente_id: int (opcional)
        estado: str (opcional)
    
    Returns:
        dict: Diccionario con todas las estadísticas
    """
    stats = EstadisticasVentas(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        cliente_id=cliente_id,
        estado=estado
    )
    return stats.obtener_estadisticas_completas()
