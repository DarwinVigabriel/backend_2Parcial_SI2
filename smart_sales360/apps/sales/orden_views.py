"""
CU17: Realizar Compra (Checkout)
CU18: Historial de Órdenes
CU19: Dashboard
CU20: Notificaciones Push

ViewSets para órdenes, historial, dashboard y notificaciones
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal

from .models import Orden, OrdenItem, Cart, NotificacionPush
from .serializers import (
    OrdenSerializer, 
    OrdenCreateSerializer, 
    OrdenCheckoutSerializer,
    OrdenHistorialSerializer,
    NotificacionPushSerializer,
    NotificacionPushCreateSerializer,
)
from apps.authentication.models import Usuarios


class OrdenViewSet(viewsets.ModelViewSet):
    """
    CU17: ViewSet para manejar órdenes (Checkout)
    
    Operaciones:
    - POST /orders/ - Crear orden desde carrito
    - GET /orders/ - Listar órdenes del usuario
    - POST /orders/{id}/checkout/ - Procesar checkout con Stripe
    - GET /orders/{id}/ - Obtener detalle de orden
    """
    serializer_class = OrdenSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Solo mostrar órdenes del usuario autenticado"""
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Orden.objects.all()
        
        # Filtrar por usuario
        try:
            usuario = Usuarios.objects.get(user=self.request.user)
            return Orden.objects.filter(usuario=usuario).order_by('-created_at')
        except Usuarios.DoesNotExist:
            return Orden.objects.none()
    
    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'create':
            return OrdenCreateSerializer
        elif self.action == 'checkout':
            return OrdenCheckoutSerializer
        return OrdenSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Crear una orden desde un carrito
        POST /orders/
        Body: {
            "carrito_id": "uuid"
        }
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        orden = serializer.save()
        
        # Retornar orden creada
        output_serializer = OrdenSerializer(orden)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        """
        CU17: Procesar checkout con Stripe
        POST /orders/{id}/checkout/
        
        Retorna session_id de Stripe para redirigir al checkout
        """
        orden = self.get_object()
        
        # Validar que la orden pertenezca al usuario
        try:
            usuario = Usuarios.objects.get(user=request.user)
            if orden.usuario != usuario:
                return Response(
                    {'detail': 'No tienes permiso para acceder a esta orden'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Usuarios.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Procesar checkout
        serializer = OrdenCheckoutSerializer(data={'orden_id': pk}, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        return Response(result, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def confirmar_pago(self, request, pk=None):
        """
        Confirmar que el pago se completó en Stripe
        POST /orders/{id}/confirmar_pago/
        Body: {
            "metodo_pago": "card",
            "stripe_payment_intent_id": "pi_xxx"
        }
        """
        orden = self.get_object()
        
        # Validar propietario
        try:
            usuario = Usuarios.objects.get(user=request.user)
            if orden.usuario != usuario:
                return Response(
                    {'detail': 'No tienes permiso para acceder a esta orden'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Usuarios.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Actualizar orden
        orden.estado = 'pagada'
        orden.pagada_en = timezone.now()
        orden.metodo_pago = request.data.get('metodo_pago', 'tarjeta')
        orden.stripe_payment_intent_id = request.data.get('stripe_payment_intent_id', '')
        orden.save()
        
        # Crear notificación
        NotificacionPush.objects.create(
            usuario=orden.usuario,
            titulo='Compra Completada',
            mensaje=f'Tu orden #{orden.numero_orden} por ${orden.total} ha sido pagada exitosamente',
            tipo='compra',
            estado='pendiente',
            datos_adicionales={'orden_id': str(orden.id)}
        )
        
        serializer = OrdenSerializer(orden)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrdenHistorialViewSet(viewsets.ReadOnlyModelViewSet):
    """
    CU18: ViewSet para historial de órdenes
    
    Operaciones:
    - GET /ordenes-historial/ - Listar historial de órdenes
    - GET /ordenes-historial/{id}/ - Obtener detalle de orden
    - GET /ordenes-historial/estadisticas/resumen/ - Estadísticas del usuario
    - GET /ordenes-historial/filtro/por-estado/?estado=pagada - Filtrar por estado
    - GET /ordenes-historial/filtro/por-rango/?fecha_inicio=2024-01-01&fecha_fin=2024-12-31 - Filtrar por rango de fechas
    """
    serializer_class = OrdenHistorialSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        CU18: Listar todas las órdenes del usuario con filtros
        """
        try:
            usuario = Usuarios.objects.get(user=self.request.user)
            queryset = Orden.objects.filter(usuario=usuario).order_by('-created_at')
        except Usuarios.DoesNotExist:
            queryset = Orden.objects.none()
        
        # Filtros opcionales
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        fecha_inicio = self.request.query_params.get('fecha_inicio', None)
        if fecha_inicio:
            queryset = queryset.filter(created_at__gte=fecha_inicio)
        
        fecha_fin = self.request.query_params.get('fecha_fin', None)
        if fecha_fin:
            queryset = queryset.filter(created_at__lte=fecha_fin)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def estadisticas_resumen(self, request):
        """
        CU18: Obtener estadísticas de compras del usuario
        GET /ordenes-historial/estadisticas-resumen/
        
        Retorna:
        {
            "total_ordenes": 5,
            "total_gastado": 1500.00,
            "promedio_orden": 300.00,
            "ordenes_pendientes": 1,
            "ordenes_pagadas": 4,
            "ultima_orden": "2024-01-15",
            "producto_mas_comprado": "Laptop"
        }
        """
        try:
            usuario = Usuarios.objects.get(user=request.user)
            ordenes = Orden.objects.filter(usuario=usuario)
            
            # Calcular estadísticas
            total_ordenes = ordenes.count()
            total_gastado = ordenes.aggregate(Sum('total'))['total__sum'] or Decimal('0')
            promedio_orden = total_gastado / total_ordenes if total_ordenes > 0 else Decimal('0')
            
            ordenes_pendientes = ordenes.filter(estado='pendiente').count()
            ordenes_pagadas = ordenes.filter(estado='pagada').count()
            
            ultima_orden = ordenes.first()
            
            # Producto más comprado
            from django.db.models import Count
            from .models import OrdenItem
            
            producto_mas_comprado = None
            items = OrdenItem.objects.filter(orden__usuario=usuario).values('producto__nombre').annotate(
                total=Count('id')
            ).order_by('-total').first()
            
            if items:
                producto_mas_comprado = items['producto__nombre']
            
            return Response({
                'total_ordenes': total_ordenes,
                'total_gastado': str(total_gastado),
                'promedio_orden': str(promedio_orden),
                'ordenes_pendientes': ordenes_pendientes,
                'ordenes_pagadas': ordenes_pagadas,
                'ordenes_confirmadas': ordenes.filter(estado='confirmada').count(),
                'ultima_orden_fecha': ultima_orden.created_at if ultima_orden else None,
                'ultima_orden_total': str(ultima_orden.total) if ultima_orden else None,
                'producto_mas_comprado': producto_mas_comprado,
            }, status=status.HTTP_200_OK)
        
        except Usuarios.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def por_estado(self, request):
        """
        CU18: Filtrar órdenes por estado
        GET /ordenes-historial/por-estado/?estado=pagada
        """
        try:
            usuario = Usuarios.objects.get(user=request.user)
            estado = request.query_params.get('estado', 'pagada')
            
            ordenes = Orden.objects.filter(usuario=usuario, estado=estado).order_by('-created_at')
            serializer = OrdenHistorialSerializer(ordenes, many=True)
            
            return Response({
                'total': ordenes.count(),
                'estado': estado,
                'ordenes': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Usuarios.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def por_rango_fechas(self, request):
        """
        CU18: Filtrar órdenes por rango de fechas
        GET /ordenes-historial/por-rango-fechas/?fecha_inicio=2024-01-01&fecha_fin=2024-12-31
        """
        try:
            usuario = Usuarios.objects.get(user=request.user)
            fecha_inicio = request.query_params.get('fecha_inicio')
            fecha_fin = request.query_params.get('fecha_fin')
            
            queryset = Orden.objects.filter(usuario=usuario)
            
            if fecha_inicio:
                queryset = queryset.filter(created_at__gte=fecha_inicio)
            if fecha_fin:
                queryset = queryset.filter(created_at__lte=fecha_fin)
            
            ordenes = queryset.order_by('-created_at')
            serializer = OrdenHistorialSerializer(ordenes, many=True)
            
            return Response({
                'total': ordenes.count(),
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'ordenes': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Usuarios.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class DashboardViewSet(viewsets.ViewSet):
    """
    CU19: ViewSet para Dashboard resumido en móvil
    
    Operaciones:
    - GET /dashboard/resumen/ - Resumen rápido
    - GET /dashboard/ultimas-compras/ - Últimas 5 compras
    - GET /dashboard/estadisticas/ - Estadísticas generales
    - GET /dashboard/alertas/ - Alertas importantes
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """
        CU19: Obtener resumen general del dashboard
        GET /dashboard/resumen/
        
        Retorna info general para mostrar en la pantalla principal
        """
        try:
            usuario = Usuarios.objects.get(user=request.user)
            ordenes = Orden.objects.filter(usuario=usuario)
            
            # Calcular totales
            total_vendido = ordenes.aggregate(Sum('total'))['total__sum'] or Decimal('0')
            total_ordenes = ordenes.count()
            promedio_venta = total_vendido / total_ordenes if total_ordenes > 0 else Decimal('0')
            
            return Response({
                'total_vendido': str(total_vendido),
                'total_ordenes': total_ordenes,
                'promedio_venta': str(promedio_venta),
                'usuario_nombre': usuario.nombre,
                'empresa': usuario.empresa.nombre if usuario.empresa else None,
            }, status=status.HTTP_200_OK)
        
        except Usuarios.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def ultimas_compras(self, request):
        """
        CU19: Obtener últimas 5 compras del usuario
        GET /dashboard/ultimas-compras/
        """
        try:
            usuario = Usuarios.objects.get(user=request.user)
            ordenes = Orden.objects.filter(usuario=usuario).order_by('-created_at')[:5]
            
            serializer = OrdenHistorialSerializer(ordenes, many=True)
            return Response({
                'cantidad': ordenes.count(),
                'ordenes': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Usuarios.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        CU19: Obtener estadísticas detalladas para el dashboard
        GET /dashboard/estadisticas/
        """
        try:
            usuario = Usuarios.objects.get(user=request.user)
            ordenes = Orden.objects.filter(usuario=usuario)
            
            # Estadísticas por estado
            ventas_pendientes = ordenes.filter(estado='pendiente').count()
            ventas_pagadas = ordenes.filter(estado='pagada').count()
            ventas_en_proceso = ordenes.filter(estado__in=['confirmada', 'enviada']).count()
            ventas_entregadas = ordenes.filter(estado='entregada').count()
            
            # Montos
            total_vendido = ordenes.aggregate(Sum('total'))['total__sum'] or Decimal('0')
            total_pendiente = ordenes.filter(estado='pendiente').aggregate(Sum('total'))['total__sum'] or Decimal('0')
            
            return Response({
                'total_vendido': str(total_vendido),
                'total_pendiente': str(total_pendiente),
                'total_ordenes': ordenes.count(),
                'estados': {
                    'pendientes': ventas_pendientes,
                    'pagadas': ventas_pagadas,
                    'en_proceso': ventas_en_proceso,
                    'entregadas': ventas_entregadas,
                }
            }, status=status.HTTP_200_OK)
        
        except Usuarios.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def alertas(self, request):
        """
        CU19: Obtener alertas para mostrar en el dashboard
        GET /dashboard/alertas/
        """
        try:
            usuario = Usuarios.objects.get(user=request.user)
            alertas = []
            
            # Alerta: Órdenes pendientes de pago
            ordenes_pendientes = Orden.objects.filter(usuario=usuario, estado='pendiente').count()
            if ordenes_pendientes > 0:
                alertas.append({
                    'tipo': 'pendiente_pago',
                    'titulo': 'Órdenes Pendientes de Pago',
                    'mensaje': f'Tienes {ordenes_pendientes} orden(es) pendiente(s) de pago',
                    'cantidad': ordenes_pendientes,
                    'nivel': 'warning'
                })
            
            # Alerta: Órdenes en proceso
            ordenes_en_proceso = Orden.objects.filter(usuario=usuario, estado='enviada').count()
            if ordenes_en_proceso > 0:
                alertas.append({
                    'tipo': 'en_proceso',
                    'titulo': 'Órdenes en Tránsito',
                    'mensaje': f'Tienes {ordenes_en_proceso} orden(es) en tránsito',
                    'cantidad': ordenes_en_proceso,
                    'nivel': 'info'
                })
            
            # Alerta: Nueva orden (si fue creada hace poco)
            ultima_orden = Orden.objects.filter(usuario=usuario).order_by('-created_at').first()
            if ultima_orden:
                tiempo_transcurrido = timezone.now() - ultima_orden.created_at
                if tiempo_transcurrido.total_seconds() < 300:  # Menos de 5 minutos
                    alertas.append({
                        'tipo': 'nueva_orden',
                        'titulo': 'Nueva Orden Creada',
                        'mensaje': f'Orden #{ultima_orden.numero_orden} creada hace poco',
                        'cantidad': 1,
                        'nivel': 'success'
                    })
            
            return Response({
                'cantidad_alertas': len(alertas),
                'alertas': alertas
            }, status=status.HTTP_200_OK)
        
        except Usuarios.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class NotificacionPushMobileViewSet(viewsets.ModelViewSet):
    """
    CU20: ViewSet para Notificaciones Push (versión mobile)
    
    Operaciones:
    - GET /notificaciones-push/ - Listar notificaciones del usuario
    - GET /notificaciones-push/sin-leer/ - Listar solo no leídas
    - POST /notificaciones-push/{id}/marcar-entregada/ - Marcar como entregada
    - DELETE /notificaciones-push/{id}/ - Eliminar notificación
    """
    serializer_class = NotificacionPushSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Mostrar solo notificaciones del usuario autenticado"""
        try:
            usuario = Usuarios.objects.get(user=self.request.user)
            return NotificacionPush.objects.filter(usuario=usuario).order_by('-created_at')
        except Usuarios.DoesNotExist:
            return NotificacionPush.objects.none()
    
    @action(detail=False, methods=['get'])
    def sin_leer(self, request):
        """
        CU20: Obtener notificaciones sin leer
        GET /notificaciones-push/sin-leer/
        """
        try:
            usuario = Usuarios.objects.get(user=request.user)
            notificaciones = NotificacionPush.objects.filter(
                usuario=usuario,
                estado__in=['pendiente', 'enviada']
            ).order_by('-created_at')
            
            serializer = NotificacionPushSerializer(notificaciones, many=True)
            return Response({
                'cantidad': notificaciones.count(),
                'notificaciones': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Usuarios.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def marcar_entregada(self, request, pk=None):
        """
        CU20: Marcar notificación como entregada
        POST /notificaciones-push/{id}/marcar-entregada/
        """
        notificacion = self.get_object()
        notificacion.marcar_entregada()
        
        serializer = NotificacionPushSerializer(notificacion)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def limpiar_leidas(self, request):
        """
        CU20: Eliminar todas las notificaciones leídas
        POST /notificaciones-push/limpiar-leidas/
        """
        try:
            usuario = Usuarios.objects.get(user=request.user)
            notificaciones_eliminadas = NotificacionPush.objects.filter(
                usuario=usuario,
                estado__in=['entregada']
            ).delete()
            
            return Response({
                'notificaciones_eliminadas': notificaciones_eliminadas[0]
            }, status=status.HTTP_200_OK)
        
        except Usuarios.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
