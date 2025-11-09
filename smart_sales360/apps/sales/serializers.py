from rest_framework import serializers
from .models import Cart, CartItem, Venta, VentaDetalle, Pago
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
