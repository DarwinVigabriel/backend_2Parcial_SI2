from rest_framework import serializers
from .models import Cart, CartItem, Venta, VentaDetalle, Pago, NotificacionPush, Reporte, PromptFrecuente, ModeloIA, Prediccion
from apps.authentication.models import DispositivosMoviles
from apps.products.serializers import ProductoSerializer
from apps.products.models import Productos
from apps.clients.models import Clientes
from decimal import Decimal


class CartItemSerializer(serializers.ModelSerializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Productos.objects.all())
    cart = serializers.PrimaryKeyRelatedField(read_only=True)
    producto_detail = ProductoSerializer(source='producto', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'producto', 'producto_detail', 'quantity', 'price', 'subtotal', 'created_at']
    
    def get_subtotal(self, obj):
        return obj.subtotal


class CartItemCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear items del carrito"""
    class Meta:
        model = CartItem
        fields = ['producto', 'quantity']
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, required=False, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'usuario', 'cliente', 'status', 'total', 'items', 'items_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total', 'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        return obj.items.count()


class VoiceCommandSerializer(serializers.Serializer):
    """Serializer para comandos de voz"""
    audio = serializers.FileField(required=True)
    cart_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate_audio(self, value):
        # Validar que sea un archivo de audio
        allowed_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm']
        file_name = value.name.lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                f"Formato de audio no soportado. Use: {', '.join(allowed_extensions)}"
            )
        
        # Validar tamaño máximo (25MB)
        if value.size > 25 * 1024 * 1024:
            raise serializers.ValidationError("El archivo de audio no debe superar los 25MB")
        
        return value


# ============================================================================
# CU12: Registrar Venta - Serializers
# ============================================================================

class VentaDetalleSerializer(serializers.ModelSerializer):
    """Serializer para detalles de venta"""
    producto_detail = ProductoSerializer(source='producto', read_only=True)
    producto_nombre = serializers.SerializerMethodField()
    producto_sku = serializers.SerializerMethodField()
    descuento_item = serializers.DecimalField(source='descuento_unitario', max_digits=12, decimal_places=2)
    
    class Meta:
        model = VentaDetalle
        fields = [
            'id', 'producto', 'producto_detail', 'cantidad', 'precio_unitario',
            'descuento_item', 'descuento_unitario', 'subtotal', 'producto_nombre', 'producto_sku', 'created_at'
        ]
        read_only_fields = ['id', 'subtotal', 'created_at']
    
    def get_producto_nombre(self, obj):
        return obj.producto.nombre if obj.producto else None
    
    def get_producto_sku(self, obj):
        return obj.producto.sku if obj.producto else None


class VentaDetalleCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear detalles de venta"""
    descuento_item = serializers.DecimalField(source='descuento_unitario', max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        model = VentaDetalle
        fields = ['producto', 'cantidad', 'precio_unitario', 'descuento_item']
    
    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value
    
    def validate_precio_unitario(self, value):
        if value < 0:
            raise serializers.ValidationError("El precio unitario no puede ser negativo")
        return value


class VentaSerializer(serializers.ModelSerializer):
    """Serializer completo para ventas"""
    detalles = VentaDetalleSerializer(many=True, read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_entrega_display = serializers.CharField(source='get_tipo_entrega_display', read_only=True)
    numero_venta = serializers.CharField(source='codigo_venta', read_only=True)
    impuesto = serializers.DecimalField(source='iva', max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Venta
        fields = [
            'id', 'codigo_venta', 'numero_venta', 'cliente', 'cliente_nombre', 
            'usuario', 'usuario_nombre', 'subtotal', 'descuento', 'iva', 'impuesto',
            'total', 'estado', 'estado_display', 'tipo_entrega', 'tipo_entrega_display',
            'metodo_pago', 'transaccion_id', 'notas', 'direccion_entrega', 
            'fecha_venta', 'detalles', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'codigo_venta', 'created_at', 'updated_at']


class VentaCreateSerializer(serializers.Serializer):
    """
    Serializer para crear una venta desde un carrito
    """
    cart_id = serializers.UUIDField(required=True)
    cliente_id = serializers.IntegerField(required=True)
    tipo_entrega = serializers.ChoiceField(
        choices=Venta.TIPO_ENTREGA_CHOICES,
        default='local'
    )
    descuento = serializers.DecimalField(
        max_digits=12, decimal_places=2, default=0, min_value=0
    )
    impuesto_porcentaje = serializers.DecimalField(
        max_digits=5, decimal_places=2, default=0, min_value=0, max_value=100
    )
    direccion_entrega = serializers.CharField(required=False, allow_blank=True)
    notas = serializers.CharField(required=False, allow_blank=True)
    
    def validate_cart_id(self, value):
        try:
            cart = Cart.objects.get(id=value)
            if cart.status != 'open':
                raise serializers.ValidationError("El carrito no está abierto")
            if not cart.items.exists():
                raise serializers.ValidationError("El carrito está vacío")
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Carrito no encontrado")
        return value
    
    def validate_cliente_id(self, value):
        try:
            Clientes.objects.get(id=value)
        except Clientes.DoesNotExist:
            raise serializers.ValidationError("Cliente no encontrado")
        return value
    
    def create(self, validated_data):
        """
        Crear venta desde un carrito
        """
        from django.db import transaction
        
        cart = Cart.objects.get(id=validated_data['cart_id'])
        cliente = Clientes.objects.get(id=validated_data['cliente_id'])
        usuario = self.context['request'].user
        
        with transaction.atomic():
            # Calcular totales
            subtotal = sum(item.subtotal for item in cart.items.all())
            descuento = validated_data.get('descuento', 0)
            impuesto_porcentaje = validated_data.get('impuesto_porcentaje', 0)
            
            subtotal_con_descuento = subtotal - descuento
            iva = (subtotal_con_descuento * impuesto_porcentaje) / 100
            total = subtotal_con_descuento + iva
            
            # Crear venta
            venta = Venta.objects.create(
                cliente=cliente,
                usuario=usuario,
                subtotal=subtotal,
                descuento=descuento,
                iva=iva,
                total=total,
                tipo_entrega=validated_data.get('tipo_entrega', 'local'),
                direccion_entrega=validated_data.get('direccion_entrega', ''),
                notas=validated_data.get('notas', ''),
                estado='pendiente'
            )
            
            # Crear detalles de venta
            for item in cart.items.all():
                VentaDetalle.objects.create(
                    venta=venta,
                    producto=item.producto,
                    cantidad=item.quantity,
                    precio_unitario=item.price,
                    descuento_unitario=0
                )
                
                # Actualizar stock del producto
                producto = item.producto
                if producto.stock_actual is not None:
                    producto.stock_actual -= item.quantity
                    producto.save()
            
            # Cerrar carrito
            cart.status = 'completed'
            cart.save()
            
            return venta


# ============================================================================
# CU13: Procesar Pago en Línea - Serializers
# ============================================================================

class PagoSerializer(serializers.ModelSerializer):
    """Serializer completo para pagos"""
    venta_numero = serializers.CharField(source='venta.numero_venta', read_only=True)
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Pago
        fields = [
            'id', 'venta', 'venta_numero', 'monto', 'metodo_pago', 'metodo_pago_display',
            'estado', 'estado_display', 'tarjeta_ultimos_digitos', 'tarjeta_tipo',
            'qr_codigo', 'qr_imagen_url', 'numero_transaccion', 'numero_autorizacion',
            'fecha_pago', 'fecha_procesamiento', 'notas', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'numero_transaccion', 'numero_autorizacion', 'fecha_procesamiento',
            'created_at', 'updated_at'
        ]


class PagoCreateSerializer(serializers.Serializer):
    """
    Serializer para crear y procesar un pago
    """
    venta_id = serializers.UUIDField(required=True)
    monto = serializers.DecimalField(max_digits=12, decimal_places=2, required=True, min_value=0.01)
    metodo_pago = serializers.ChoiceField(choices=Pago.METODO_PAGO_CHOICES, required=True)
    
    # Campos para tarjeta
    tarjeta_numero = serializers.CharField(required=False, allow_blank=True, max_length=16, min_length=16)
    tarjeta_nombre = serializers.CharField(required=False, allow_blank=True, max_length=100)
    tarjeta_expiracion = serializers.CharField(required=False, allow_blank=True, max_length=5)  # MM/YY
    tarjeta_cvv = serializers.CharField(required=False, allow_blank=True, max_length=4, min_length=3)
    
    # Notas adicionales
    notas = serializers.CharField(required=False, allow_blank=True)
    
    def validate_venta_id(self, value):
        try:
            venta = Venta.objects.get(id=value)
            if venta.estado == 'pagada':
                raise serializers.ValidationError("Esta venta ya ha sido pagada")
            if venta.estado == 'cancelada':
                raise serializers.ValidationError("Esta venta ha sido cancelada")
        except Venta.DoesNotExist:
            raise serializers.ValidationError("Venta no encontrada")
        return value
    
    def validate(self, data):
        # Validar campos de tarjeta si el método es tarjeta
        if data['metodo_pago'] in ['tarjeta_credito', 'tarjeta_debito']:
            if not data.get('tarjeta_numero'):
                raise serializers.ValidationError({
                    'tarjeta_numero': 'El número de tarjeta es requerido'
                })
            if not data.get('tarjeta_nombre'):
                raise serializers.ValidationError({
                    'tarjeta_nombre': 'El nombre del titular es requerido'
                })
            if not data.get('tarjeta_expiracion'):
                raise serializers.ValidationError({
                    'tarjeta_expiracion': 'La fecha de expiración es requerida'
                })
            if not data.get('tarjeta_cvv'):
                raise serializers.ValidationError({
                    'tarjeta_cvv': 'El CVV es requerido'
                })
            
            # Validar formato de tarjeta (básico)
            if not data['tarjeta_numero'].isdigit():
                raise serializers.ValidationError({
                    'tarjeta_numero': 'El número de tarjeta debe contener solo dígitos'
                })
            
            # Validar formato de expiración MM/YY
            if len(data['tarjeta_expiracion']) != 5 or data['tarjeta_expiracion'][2] != '/':
                raise serializers.ValidationError({
                    'tarjeta_expiracion': 'La fecha debe estar en formato MM/YY'
                })
            
            # Validar CVV
            if not data['tarjeta_cvv'].isdigit():
                raise serializers.ValidationError({
                    'tarjeta_cvv': 'El CVV debe contener solo dígitos'
                })
        
        return data
    
    def create(self, validated_data):
        """
        Crear y procesar el pago con Stripe
        """
        from django.db import transaction
        import os
        import stripe
        
        venta = Venta.objects.get(id=validated_data['venta_id'])
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_')
        
        with transaction.atomic():
            # Crear pago
            pago = Pago.objects.create(
                venta=venta,
                monto=validated_data['monto'],
                metodo_pago=validated_data['metodo_pago'],
                estado='pendiente',
                notas=validated_data.get('notas', '')
            )
            
            # Procesar información según método de pago
            if validated_data['metodo_pago'] in ['tarjeta_credito', 'tarjeta_debito']:
                # Guardar solo últimos 4 dígitos (enmascarar)
                tarjeta_numero = validated_data.get('tarjeta_numero', '')
                pago.tarjeta_ultimos_digitos = tarjeta_numero[-4:] if tarjeta_numero else None
                
                # Detectar tipo de tarjeta usando Stripe
                if tarjeta_numero.startswith('4'):
                    pago.tarjeta_tipo = 'Visa'
                elif tarjeta_numero.startswith('5'):
                    pago.tarjeta_tipo = 'Mastercard'
                elif tarjeta_numero.startswith('3'):
                    pago.tarjeta_tipo = 'American Express'
                elif tarjeta_numero.startswith('6'):
                    pago.tarjeta_tipo = 'Discover'
                else:
                    pago.tarjeta_tipo = 'Desconocida'
                
                pago.save()
            
            elif validated_data['metodo_pago'] == 'qr':
                # Generar código QR para pago
                pago.qr_codigo = f'QR-{venta.id}-{pago.id}'
                pago.qr_imagen_url = f'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={pago.qr_codigo}'
                pago.save()
            
            # Procesar el pago con Stripe
            pago.procesar_pago()
            
            return pago


class PagoQRSerializer(serializers.Serializer):
    """
    Serializer para generar un código QR de pago
    """
    venta_id = serializers.UUIDField(required=True)
    
    def validate_venta_id(self, value):
        try:
            venta = Venta.objects.get(id=value)
            if venta.estado == 'pagada':
                raise serializers.ValidationError("Esta venta ya ha sido pagada")
        except Venta.DoesNotExist:
            raise serializers.ValidationError("Venta no encontrada")
        return value
    
    def create(self, validated_data):
        """
        Generar código QR para pago
        """
        import random
        
        venta = Venta.objects.get(id=validated_data['venta_id'])
        
        # Generar código QR único
        qr_codigo = f'QR-{venta.numero_venta}-{random.randint(100000, 999999)}'
        qr_imagen_url = f'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_codigo}'
        
        return {
            'qr_codigo': qr_codigo,
            'qr_imagen_url': qr_imagen_url,
            'venta_numero': venta.numero_venta,
            'monto': str(venta.total)
        }


# CU14: Serializer para descargar comprobante PDF
class ComprobanteDescargarSerializer(serializers.Serializer):
    """Serializer para descargar comprobante de venta en PDF"""
    venta_id = serializers.IntegerField(required=True)
    
    def validate_venta_id(self, value):
        try:
            Venta.objects.get(id=value)
        except Venta.DoesNotExist:
            raise serializers.ValidationError("Venta no encontrada")
        return value


# CU15 & CU16: Serializers para reportes y estadísticas
class VentaListadoSerializer(serializers.ModelSerializer):
    """Serializer para listar ventas con información completa"""
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    vendedor_nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    total_detalles = serializers.SerializerMethodField()
    
    class Meta:
        model = Venta
        fields = [
            'id', 'codigo_venta', 'cliente_nombre', 'vendedor_nombre',
            'subtotal', 'descuento', 'iva', 'total', 'estado',
            'metodo_pago', 'total_detalles', 'fecha_venta', 'created_at'
        ]
    
    def get_total_detalles(self, obj):
        return obj.detalles.count()


class EstadisticasVentasSerializer(serializers.Serializer):
    """Serializer para estadísticas de ventas (CU16)"""
    total_vendido = serializers.DecimalField(max_digits=15, decimal_places=2)
    cantidad_ventas = serializers.IntegerField()
    promedio_por_venta = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_descuentos = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_impuestos = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Por estado
    ventas_pendientes = serializers.IntegerField()
    ventas_pagadas = serializers.IntegerField()
    ventas_canceladas = serializers.IntegerField()
    
    # Por método de pago
    ventas_tarjeta = serializers.IntegerField()
    ventas_efectivo = serializers.IntegerField()
    ventas_transferencia = serializers.IntegerField()
    ventas_otros = serializers.IntegerField()
    
    
    # Top productos
    top_productos = serializers.ListField()
    
    # Tendencia
    periodo = serializers.CharField()
    fecha_inicio = serializers.DateTimeField()
    fecha_fin = serializers.DateTimeField()


# CU17-19: Serializers para móvil
class DispositivoMovilSerializer(serializers.ModelSerializer):
    """Serializer para dispositivos móviles"""
    class Meta:
        model = DispositivosMoviles
        fields = [
            'id', 'usuario', 'device_id', 'device_token', 'plataforma',
            'modelo_dispositivo', 'os_version', 'activo', 'app_version',
            'last_activity', 'idioma', 'timezone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VentaMovilSerializer(serializers.ModelSerializer):
    """
    CU17: Serializer para crear ventas desde dispositivos móviles
    Versión simplificada con campos esenciales
    """
    detalles = VentaDetalleSerializer(many=True, read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    
    class Meta:
        model = Venta
        fields = [
            'id', 'codigo_venta', 'cliente', 'cliente_nombre', 'usuario',
            'subtotal', 'descuento', 'iva', 'total', 'estado', 'metodo_pago',
            'tipo_entrega', 'direccion_entrega', 'notas', 'fecha_venta',
            'detalles', 'created_at'
        ]
        read_only_fields = ['id', 'codigo_venta', 'created_at', 'fecha_venta']


class VentaCreateMovilSerializer(serializers.ModelSerializer):
    """
    CU17: Serializer para crear ventas desde móvil
    """
    detalles_datos = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="Array de {producto_id, cantidad, precio}"
    )
    
    class Meta:
        model = Venta
        fields = [
            'cliente', 'usuario', 'subtotal', 'descuento', 'iva', 'total',
            'estado', 'metodo_pago', 'transaccion_id', 'tipo_entrega',
            'direccion_entrega', 'notas', 'detalles_datos'
        ]
    
    def create(self, validated_data):
        detalles_datos = validated_data.pop('detalles_datos', [])
        venta = Venta.objects.create(**validated_data)
        
        # Crear detalles de venta
        for detalle_data in detalles_datos:
            VentaDetalle.objects.create(venta=venta, **detalle_data)
        
        return venta


class VentaHistoricoMovilSerializer(serializers.ModelSerializer):
    """
    CU18: Serializer para historial de compras (versión mobile)
    """
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    detalles_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Venta
        fields = [
            'id', 'codigo_venta', 'cliente', 'cliente_nombre', 'total',
            'estado', 'metodo_pago', 'tipo_entrega', 'fecha_venta',
            'detalles_count', 'created_at'
        ]
        read_only_fields = fields
    
    def get_detalles_count(self, obj):
        return obj.detalles.count()


class DashboardMovilSerializer(serializers.Serializer):
    """
    CU19: Serializer para Dashboard resumido en móvil
    """
    # Resumen rápido
    total_vendido = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_ventas = serializers.IntegerField()
    promedio_venta = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Últimas ventas
    ultimas_ventas = VentaHistoricoMovilSerializer(many=True)
    
    # Estadísticas rápidas
    ventas_pendientes = serializers.IntegerField()
    ventas_pagadas = serializers.IntegerField()
    ventas_en_proceso = serializers.IntegerField()
    
    # Alertas
    alertas = serializers.ListField(child=serializers.DictField())


class NotificacionPushSerializer(serializers.ModelSerializer):
    """
    CU20: Serializer para notificaciones push
    """
    usuario_nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True, allow_null=True)
    
    class Meta:
        model = NotificacionPush
        fields = [
            'id', 'usuario', 'usuario_nombre', 'cliente', 'cliente_nombre',
            'venta', 'titulo', 'mensaje', 'tipo', 'estado', 'datos_adicionales',
            'fecha_envio', 'fecha_entrega', 'intentos', 'error_mensaje',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'fecha_envio', 'fecha_entrega', 'intentos', 'error_mensaje',
            'created_at', 'updated_at', 'usuario_nombre', 'cliente_nombre'
        ]


class NotificacionPushCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear notificaciones push
    """
    class Meta:
        model = NotificacionPush
        fields = [
            'usuario', 'cliente', 'venta', 'titulo', 'mensaje', 'tipo',
            'datos_adicionales'
        ]


# ============================================================================
# CU21, CU22, CU23: Serializers para Reportes Dinámicos y Exportación
# ============================================================================

class ReporteSerializer(serializers.ModelSerializer):
    """
    Serializer completo para Reportes (CU21, CU22, CU23)
    """
    usuario_nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    tipo_reporte_display = serializers.CharField(source='get_tipo_reporte_display', read_only=True)
    formato_display = serializers.CharField(source='get_formato_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Reporte
        fields = [
            'id', 'usuario', 'usuario_nombre', 'titulo', 'tipo_reporte', 'tipo_reporte_display',
            'formato', 'formato_display', 'filtros', 'datos_reporte', 'resumen_texto',
            'resumen_voz', 'archivo_pdf', 'archivo_excel', 'archivo_csv',
            'estado', 'estado_display', 'error_mensaje', 'total_registros',
            'tiempo_generacion', 'fecha_generacion', 'fecha_ultimaDescarga',
            'descargas', 'created_at'
        ]
        read_only_fields = [
            'id', 'usuario_nombre', 'datos_reporte', 'resumen_texto', 'resumen_voz',
            'archivo_pdf', 'archivo_excel', 'archivo_csv', 'estado', 'error_mensaje',
            'total_registros', 'tiempo_generacion', 'fecha_generacion', 'fecha_ultimaDescarga',
            'descargas', 'created_at'
        ]


class ReporteGenerarSerializer(serializers.Serializer):
    """
    Serializer para generar nuevos reportes (CU21, CU22, CU23)
    Permite especificar tipo de reporte, filtros y formato de salida
    """
    titulo = serializers.CharField(max_length=255, required=True, help_text="Título personalizado del reporte")
    tipo_reporte = serializers.ChoiceField(
        choices=Reporte.TIPO_REPORTE_CHOICES,
        required=True,
        help_text="Tipo de reporte a generar"
    )
    formato = serializers.ChoiceField(
        choices=Reporte.FORMATO_CHOICES,
        required=False,
        default='pdf',
        help_text="Formato de salida del reporte"
    )
    
    # Filtros para reporte de ventas
    fecha_inicio = serializers.DateField(required=False, allow_null=True, help_text="Fecha inicio del período")
    fecha_fin = serializers.DateField(required=False, allow_null=True, help_text="Fecha fin del período")
    
    # Filtros por cliente
    cliente_id = serializers.IntegerField(required=False, allow_null=True)
    cliente_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Array de IDs de clientes para filtrar"
    )
    
    # Filtros por producto
    producto_id = serializers.IntegerField(required=False, allow_null=True)
    producto_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Array de IDs de productos para filtrar"
    )
    
    # Filtros por estado
    estado_venta = serializers.CharField(required=False, allow_blank=True)
    metodo_pago = serializers.CharField(required=False, allow_blank=True)
    
    # Opciones de generación
    incluir_graficas = serializers.BooleanField(default=True, help_text="Incluir gráficas en el reporte")
    incluir_resumen = serializers.BooleanField(default=True, help_text="Incluir resumen ejecutivo")
    incluir_voz = serializers.BooleanField(default=False, help_text="Generar versión en voz (MP3)")
    
    # Agrupación (para análisis)
    agrupar_por = serializers.ChoiceField(
        choices=[
            ('diario', 'Diario'),
            ('semanal', 'Semanal'),
            ('mensual', 'Mensual'),
            ('cliente', 'Cliente'),
            ('producto', 'Producto'),
            ('vendedor', 'Vendedor'),
        ],
        required=False,
        allow_blank=True,
        help_text="Agrupación de datos para análisis"
    )
    
    def validate(self, data):
        """Validaciones adicionales"""
        # Si se especifica cliente_id, no se puede especificar cliente_ids
        if data.get('cliente_id') and data.get('cliente_ids'):
            raise serializers.ValidationError(
                "No se puede especificar cliente_id y cliente_ids simultáneamente"
            )
        
        # Si se especifica producto_id, no se puede especificar producto_ids
        if data.get('producto_id') and data.get('producto_ids'):
            raise serializers.ValidationError(
                "No se puede especificar producto_id y producto_ids simultáneamente"
            )
        
        return data


class ReporteListadoSerializer(serializers.ModelSerializer):
    """
    Serializer para listar reportes generados (CU21)
    """
    usuario_nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    tipo_reporte_display = serializers.CharField(source='get_tipo_reporte_display', read_only=True)
    formato_display = serializers.CharField(source='get_formato_display', read_only=True)
    
    class Meta:
        model = Reporte
        fields = [
            'id', 'titulo', 'usuario_nombre', 'tipo_reporte', 'tipo_reporte_display',
            'formato', 'formato_display', 'estado', 'total_registros', 'descargas',
            'fecha_generacion', 'fecha_ultimaDescarga'
        ]
        read_only_fields = fields


class ReporteExportarSerializer(serializers.Serializer):
    """
    Serializer para exportar/descargar reporte en diferentes formatos (CU23)
    """
    formato = serializers.ChoiceField(
        choices=Reporte.FORMATO_CHOICES,
        required=True,
        help_text="Formato de exportación: pdf, excel, csv, json"
    )
    incluir_graficas = serializers.BooleanField(
        default=True,
        help_text="Incluir gráficas en PDF (solo aplica para PDF)"
    )


class ReporteVozSerializer(serializers.Serializer):
    """
    Serializer para generar resumen en voz del reporte (CU22)
    """
    velocidad = serializers.FloatField(
        default=1.0,
        min_value=0.5,
        max_value=2.0,
        help_text="Velocidad de reproducción (0.5 a 2.0)"
    )
    idioma = serializers.ChoiceField(
        choices=[
            ('es', 'Español'),
            ('en', 'Inglés'),
            ('fr', 'Francés'),
        ],
        default='es',
        help_text="Idioma del resumen en voz"
    )
    regenerar = serializers.BooleanField(
        default=False,
        help_text="Forzar regeneración del audio si ya existe"
    )


# ============================================================================
# CU24: Serializers para Prompts Frecuentes
# ============================================================================

class PromptFrecuenteSerializer(serializers.ModelSerializer):
    """Serializer completo para Prompts Frecuentes (CU24)"""
    usuario_nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    tipo_reporte_display = serializers.CharField(source='get_tipo_reporte_display', read_only=True)
    formato_display = serializers.CharField(source='get_formato_display', read_only=True)
    
    class Meta:
        model = PromptFrecuente
        fields = [
            'id', 'usuario', 'usuario_nombre', 'nombre', 'descripcion', 'categoria',
            'categoria_display', 'tipo_reporte', 'tipo_reporte_display', 'formato',
            'formato_display', 'filtros', 'opciones', 'veces_usado', 'ultima_utilizacion',
            'activo', 'favorito', 'created_at'
        ]
        read_only_fields = [
            'id', 'usuario_nombre', 'veces_usado', 'ultima_utilizacion', 'created_at'
        ]


class PromptFrecuenteCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar prompts frecuentes"""
    class Meta:
        model = PromptFrecuente
        fields = [
            'nombre', 'descripcion', 'categoria', 'tipo_reporte', 'formato',
            'filtros', 'opciones', 'activo', 'favorito'
        ]


# ============================================================================
# CU26: Serializers para Modelo IA
# ============================================================================

class ModeloIASerializer(serializers.ModelSerializer):
    """Serializer para Modelos IA (CU26)"""
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    algoritmo_display = serializers.CharField(source='get_algoritmo_display', read_only=True)
    variable_objetivo_display = serializers.CharField(source='get_variable_objetivo_display', read_only=True)
    
    class Meta:
        model = ModeloIA
        fields = [
            'id', 'nombre', 'descripcion', 'algoritmo', 'algoritmo_display',
            'variable_objetivo', 'variable_objetivo_display', 'estado', 'estado_display',
            'fecha_entrenamiento', 'datos_entrenamiento', 'periodo_entrenamiento',
            'precision', 'mae', 'rmse', 'r_squared', 'parametros', 'error_mensaje',
            'creado_por', 'creado_por_nombre', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'id', 'fecha_entrenamiento', 'datos_entrenamiento', 'precision', 'mae',
            'rmse', 'r_squared', 'error_mensaje', 'creado_por_nombre', 'creado_en', 'actualizado_en'
        ]


class ModeloIAEntrenarSerializer(serializers.Serializer):
    """Serializer para entrenar un modelo (CU26)"""
    periodo_entrenamiento = serializers.ChoiceField(
        choices=[('30d', 'Últimos 30 días'), ('90d', 'Últimos 90 días'), ('180d', 'Últimos 180 días'), ('1y', 'Último año')],
        default='90d'
    )
    parametros_custom = serializers.JSONField(required=False, help_text="Parámetros personalizados")


# ============================================================================
# CU25: Serializers para Predicciones
# ============================================================================

class PrediccionSerializer(serializers.ModelSerializer):
    """Serializer para Predicciones (CU25)"""
    modelo_nombre = serializers.CharField(source='modelo.nombre', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = Prediccion
        fields = [
            'id', 'modelo', 'modelo_nombre', 'tipo', 'tipo_display',
            'fecha_prediccion', 'fecha_inicio_periodo', 'fecha_fin_periodo',
            'valor_predicho', 'intervalo_confianza_inferior', 'intervalo_confianza_superior',
            'valor_real', 'error_prediccion', 'variables_utilizadas', 'datos_complementarios'
        ]
        read_only_fields = [
            'id', 'modelo_nombre', 'fecha_prediccion', 'error_prediccion'
        ]


class PrediccionListadoSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar predicciones"""
    modelo_nombre = serializers.CharField(source='modelo.nombre', read_only=True)
    
    class Meta:
        model = Prediccion
        fields = [
            'id', 'modelo', 'modelo_nombre', 'tipo', 'fecha_inicio_periodo',
            'fecha_fin_periodo', 'valor_predicho', 'valor_real', 'error_prediccion'
        ]