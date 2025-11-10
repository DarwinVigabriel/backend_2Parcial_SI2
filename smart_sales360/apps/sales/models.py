from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
import uuid


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey('authentication.Usuarios', models.DO_NOTHING, blank=True, null=True)
    cliente = models.ForeignKey('clients.Clientes', models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=20, default='open')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'carts'


class CartItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    cart = models.ForeignKey('sales.Cart', models.CASCADE, related_name='items')
    producto = models.ForeignKey('products.Productos', models.DO_NOTHING)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'cart_items'

    @property
    def subtotal(self):
        return (self.price or 0) * (self.quantity or 0)


class Venta(models.Model):
    """
    CU12: Registrar Venta
    Modelo principal para registrar las ventas realizadas
    """
    # Choices basados en los constraints de la base de datos
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
        ('reembolsada', 'Reembolsada'),
        ('en_proceso', 'En Proceso'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('transferencia', 'Transferencia'),
    ]
    
    TIPO_ENTREGA_CHOICES = [
        ('local', 'Retiro en Local'),
        ('domicilio', 'Entrega a Domicilio'),
        ('express', 'Entrega Express'),
    ]

    # Usar la estructura existente de la tabla
    id = models.AutoField(primary_key=True)
    codigo_venta = models.CharField(max_length=50, unique=True, editable=False)
    cliente = models.ForeignKey('clients.Clientes', models.DO_NOTHING, blank=True, null=True, related_name='ventas', db_column='cliente_id')
    usuario = models.ForeignKey('authentication.Usuarios', models.DO_NOTHING, related_name='ventas_realizadas', db_column='usuario_id')
    
    # Montos (usando nombres existentes)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Estado y tipo
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    metodo_pago = models.CharField(max_length=50, choices=METODO_PAGO_CHOICES, blank=True, null=True)
    transaccion_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Información adicional
    notas = models.TextField(blank=True, null=True)
    direccion_entrega = models.TextField(blank=True, null=True)
    tipo_entrega = models.CharField(max_length=20, choices=TIPO_ENTREGA_CHOICES, default='local')
    
    fecha_venta = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'ventas'
        ordering = ['-fecha_venta']
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'

    def __str__(self):
        return f"{self.codigo_venta} - {self.cliente.nombre_completo if self.cliente else 'Sin cliente'} - ${self.total}"
    
    @property
    def numero_venta(self):
        """Alias para mantener compatibilidad con código que usa numero_venta"""
        return self.codigo_venta
    
    @property
    def impuesto(self):
        """Alias para mantener compatibilidad con código que usa impuesto"""
        return self.iva
    
    # CU14: Métodos para generar comprobante de venta
    def generar_comprobante_pdf(self):
        """
        Genera un comprobante de venta en PDF
        Retorna un BytesIO con el archivo PDF
        """
        from .comprobante_pdf import generar_comprobante_pdf
        return generar_comprobante_pdf(self)
    
    def obtener_nombre_archivo_pdf(self):
        """Obtiene un nombre descriptivo para el archivo PDF"""
        return f"Comprobante_{self.codigo_venta}_{self.fecha_venta.strftime('%Y%m%d')}.pdf"

    def save(self, *args, **kwargs):
        # Generar código de venta automático si no existe
        if not self.codigo_venta:
            # Generar número de venta automático: V-YYYYMMDD-XXXX
            from django.db.models import Max
            today = timezone.now().strftime('%Y%m%d')
            prefix = f'V-{today}-'
            
            last_sale = Venta.objects.filter(codigo_venta__startswith=prefix).aggregate(
                Max('codigo_venta')
            )['codigo_venta__max']
            
            if last_sale:
                last_number = int(last_sale.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.codigo_venta = f'{prefix}{new_number:04d}'
        
        # Calcular totales si no están establecidos o si es una actualización
        # Solo calcular si la venta ya existe y tiene detalles
        if self.pk:
            # Venta existente: recalcular desde detalles
            detalles = self.detalles.all()
            if detalles.exists():
                self.subtotal = sum(d.subtotal for d in detalles)
                self.total = self.subtotal - (self.descuento or 0) + (self.iva or 0)
        else:
            # Venta nueva: asegurar valores por defecto
            if self.subtotal is None:
                self.subtotal = 0
            if self.total is None:
                self.total = 0
        
        super().save(*args, **kwargs)


class VentaDetalle(models.Model):
    """
    Detalle de productos vendidos en cada venta
    """
    id = models.AutoField(primary_key=True)
    venta = models.ForeignKey('sales.Venta', models.CASCADE, related_name='detalles', db_column='venta_id')
    producto = models.ForeignKey('products.Productos', models.DO_NOTHING, db_column='producto_id')
    
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'venta_detalles'
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"
    
    @property
    def descuento_item(self):
        """Alias para compatibilidad"""
        return self.descuento_unitario
    
    @property
    def producto_nombre(self):
        """Obtener nombre del producto"""
        return self.producto.nombre
    
    @property
    def producto_sku(self):
        """Obtener SKU del producto"""
        return self.producto.sku

    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = (self.precio_unitario * self.cantidad) - self.descuento_unitario
        super().save(*args, **kwargs)
        
        # Actualizar totales de la venta padre
        if self.venta_id:
            self.actualizar_totales_venta()
    
    def actualizar_totales_venta(self):
        """Recalcular los totales de la venta basándose en todos sus detalles"""
        venta = self.venta
        detalles = venta.detalles.all()
        venta.subtotal = sum(d.subtotal for d in detalles)
        venta.total = venta.subtotal - (venta.descuento or 0) + (venta.iva or 0)
        venta.save()


# Señal para actualizar totales cuando se elimina un detalle
@receiver(post_delete, sender=VentaDetalle)
def actualizar_totales_al_eliminar(sender, instance, **kwargs):
    """Actualizar totales de la venta cuando se elimina un detalle"""
    if instance.venta_id:
        venta = instance.venta
        detalles = venta.detalles.all()
        venta.subtotal = sum(d.subtotal for d in detalles) if detalles.exists() else 0
        venta.total = venta.subtotal - (venta.descuento or 0) + (venta.iva or 0)
        venta.save()


class Pago(models.Model):
    """
    CU13: Procesar Pago en Línea
    Modelo para registrar los pagos de las ventas
    """
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('qr', 'Código QR'),
        ('paypal', 'PayPal'),
        ('otro', 'Otro'),
    ]
    
    ESTADO_PAGO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
        ('reembolsado', 'Reembolsado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venta = models.ForeignKey('sales.Venta', models.CASCADE, related_name='pagos')
    
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, default='pendiente')
    
    # Información de la tarjeta (simulado/enmascarado)
    tarjeta_ultimos_digitos = models.CharField(max_length=4, blank=True, null=True)
    tarjeta_tipo = models.CharField(max_length=20, blank=True, null=True)  # Visa, Mastercard, etc.
    
    # Información de QR
    qr_codigo = models.CharField(max_length=100, blank=True, null=True)
    qr_imagen_url = models.TextField(blank=True, null=True)
    
    # Información de transacción
    numero_transaccion = models.CharField(max_length=100, unique=True, editable=False)
    numero_autorizacion = models.CharField(max_length=100, blank=True, null=True)
    
    # Fechas
    fecha_pago = models.DateTimeField(default=timezone.now)
    fecha_procesamiento = models.DateTimeField(blank=True, null=True)
    
    # Adicional
    notas = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'pagos'
        ordering = ['-fecha_pago']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago {self.numero_transaccion} - {self.get_metodo_pago_display()} - ${self.monto}"

    def save(self, *args, **kwargs):
        if not self.numero_transaccion:
            # Generar número de transacción: PAY-YYYYMMDDHHMMSS-XXXX
            from django.db.models import Max
            import random
            
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_suffix = random.randint(1000, 9999)
            self.numero_transaccion = f'PAY-{timestamp}-{random_suffix}'
        
        super().save(*args, **kwargs)

    def procesar_pago(self):
        """
        Procesa el pago usando Stripe
        Integración real con Stripe para procesar tarjetas y otros métodos de pago
        """
        import os
        import stripe
        from decimal import Decimal
        
        try:
            # Configurar clave secreta de Stripe
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_')
            
            self.estado = 'procesando'
            self.save()
            
            # Determinar tipo de método de pago para Stripe
            if self.metodo_pago in ['tarjeta_credito', 'tarjeta_debito']:
                # Procesar pago con tarjeta
                if not self.numero_transaccion.startswith('pi_'):
                    # Crear un Payment Intent en Stripe
                    try:
                        payment_intent = stripe.PaymentIntent.create(
                            amount=int(self.monto * 100),  # Stripe usa centavos
                            currency='usd',
                            payment_method_types=['card'],
                            description=f'Pago para venta {self.venta.codigo_venta}',
                            metadata={
                                'venta_id': self.venta.id,
                                'pago_id': str(self.id),
                                'cliente': self.venta.cliente.nombre_completo if self.venta.cliente else 'Sin cliente',
                            }
                        )
                        self.numero_transaccion = payment_intent['id']
                        
                        # En un sistema real, aquí se confirmaría el pago del cliente
                        # Por ahora, simulamos un pago exitoso
                        confirmed_intent = stripe.PaymentIntent.confirm(
                            payment_intent['id'],
                            payment_method='pm_card_visa'  # Test token de Stripe
                        )
                        
                        if confirmed_intent['status'] == 'succeeded':
                            self.estado = 'completado'
                            self.fecha_procesamiento = timezone.now()
                            self.numero_autorizacion = confirmed_intent['charges']['data'][0]['id'] if confirmed_intent['charges']['data'] else f'STRIPE-{self.numero_transaccion}'
                        else:
                            self.estado = 'fallido'
                            self.notas = f"Pago rechazado por Stripe: {confirmed_intent['status']}"
                    except Exception as e:
                        self.estado = 'fallido'
                        self.notas = f"Error de Stripe en tarjeta: {str(e)}"
            
            elif self.metodo_pago == 'qr':
                # Procesar pago QR (generando código QR para mostrar)
                # En QR no es necesario crear PaymentIntent, simplemente generar el código
                if not self.qr_codigo:
                    self.qr_codigo = f'QR-VENTA-{self.venta.id}-{self.id}'
                
                if not self.qr_imagen_url:
                    # Generar URL de imagen QR desde qrserver
                    self.qr_imagen_url = f'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={self.qr_codigo}'
                
                # Marcar como completado
                self.estado = 'completado'
                self.fecha_procesamiento = timezone.now()
                self.numero_autorizacion = f'QR-{self.numero_transaccion}'
            
            elif self.metodo_pago == 'paypal':
                # Procesar pago con PayPal a través de Stripe
                try:
                    payment_intent = stripe.PaymentIntent.create(
                        amount=int(self.monto * 100),
                        currency='usd',
                        payment_method_types=['paypal'],
                        description=f'Pago PayPal para venta {self.venta.codigo_venta}',
                        metadata={'venta_id': self.venta.id, 'pago_id': str(self.id)}
                    )
                    self.numero_transaccion = payment_intent['id']
                    self.estado = 'completado'
                    self.fecha_procesamiento = timezone.now()
                    self.numero_autorizacion = payment_intent['id']
                except Exception as e:
                    self.estado = 'fallido'
                    self.notas = f"Error de Stripe en PayPal: {str(e)}"
            
            else:
                # Métodos de pago alternativos (efectivo, transferencia)
                # Se registran pero no se procesan con Stripe
                self.estado = 'completado'
                self.fecha_procesamiento = timezone.now()
                self.numero_autorizacion = self.numero_transaccion
            
            # Actualizar estado de la venta si el pago fue exitoso
            if self.estado == 'completado' and self.venta:
                self.venta.estado = 'pagada'
                # Mapear método de pago del Pago a los valores permitidos en Venta
                metodo_mapping = {
                    'tarjeta_credito': 'tarjeta',
                    'tarjeta_debito': 'tarjeta',
                    'qr': 'stripe',
                    'efectivo': 'efectivo',
                    'paypal': 'paypal',
                    'transferencia': 'transferencia',
                    'otro': 'efectivo',
                }
                self.venta.metodo_pago = metodo_mapping.get(self.metodo_pago, 'efectivo')
                self.venta.transaccion_id = self.numero_transaccion
                self.venta.save()
        
        except stripe.error.CardError as e:
            # Tarjeta rechazada
            self.estado = 'fallido'
            self.notas = f"Tarjeta rechazada: {e.user_message}"
        except stripe.error.RateLimitError:
            self.estado = 'fallido'
            self.notas = "Límite de velocidad de Stripe alcanzado"
        except stripe.error.InvalidRequestError as e:
            self.estado = 'fallido'
            self.notas = f"Solicitud inválida a Stripe: {e.user_message}"
        except stripe.error.AuthenticationError:
            self.estado = 'fallido'
            self.notas = "Error de autenticación con Stripe"
        except stripe.error.APIConnectionError:
            self.estado = 'fallido'
            self.notas = "Error de conexión con Stripe"
        except stripe.error.StripeError as e:
            self.estado = 'fallido'
            self.notas = f"Error de Stripe: {str(e)}"
        except Exception as e:
            self.estado = 'fallido'
            self.notas = f"Error procesando pago: {str(e)}"
        
        self.save()
        return self.estado == 'completado'


class NotificacionPush(models.Model):
    """
    CU20: Gestionar Notificaciones Push
    Modelo para almacenar notificaciones push del sistema (Tabla adicional con más detalles que Notificaciones)
    """
    TIPO_CHOICES = [
        ('venta', 'Venta Completada'),
        ('pago', 'Pago Recibido'),
        ('compra', 'Compra Realizada'),
        ('descuento', 'Descuento Disponible'),
        ('promocion', 'Promoción'),
        ('alerta', 'Alerta del Sistema'),
        ('otro', 'Otro'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviada', 'Enviada'),
        ('entregada', 'Entregada'),
        ('fallida', 'Fallida'),
    ]

    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey('authentication.Usuarios', models.CASCADE, related_name='notificaciones_push_sales')
    cliente = models.ForeignKey('clients.Clientes', models.SET_NULL, null=True, blank=True, related_name='notificaciones_push')
    venta = models.ForeignKey('sales.Venta', models.SET_NULL, null=True, blank=True, related_name='notificaciones_push', help_text="Venta relacionada a la notificación")
    
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='otro')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Datos adicionales (JSON)
    datos_adicionales = models.JSONField(default=dict, blank=True, help_text="Datos personalizados de la notificación")
    
    # Control de entrega
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    intentos = models.IntegerField(default=0)
    error_mensaje = models.TextField(blank=True, null=True)
    
    # Registro
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = True
        db_table = 'notificaciones_push_sales'
        ordering = ['-created_at']
        verbose_name = 'Notificación Push Ventas'
        verbose_name_plural = 'Notificaciones Push Ventas'
    
    def __str__(self):
        usuario_nombre = self.usuario.nombre if hasattr(self.usuario, 'nombre') else str(self.usuario)
        return f"{self.titulo} - {usuario_nombre} ({self.estado})"
    
    def marcar_enviada(self):
        """Marca la notificación como enviada"""
        self.estado = 'enviada'
        self.fecha_envio = timezone.now()
        self.save()
    
    def marcar_entregada(self):
        """Marca la notificación como entregada"""
        self.estado = 'entregada'
        self.fecha_entrega = timezone.now()
        self.save()
    
    
    def registrar_error(self, error_msg):
        """Registra un error en el envío"""
        self.intentos += 1
        self.error_mensaje = error_msg
        if self.intentos >= 3:
            self.estado = 'fallida'
        self.save()


class Reporte(models.Model):
    """
    CU21, CU22, CU23: Generación de Reportes Dinámicos
    Modelo para almacenar reportes generados con filtros y exportaciones
    """
    TIPO_REPORTE_CHOICES = [
        ('ventas', 'Reporte de Ventas'),
        ('productos', 'Reporte de Productos'),
        ('clientes', 'Reporte de Clientes'),
        ('estadisticas', 'Estadísticas Generales'),
        ('top_vendedores', 'Top Vendedores'),
        ('tendencias', 'Análisis de Tendencias'),
    ]
    
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    ESTADO_CHOICES = [
        ('generando', 'Generando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
        ('descargado', 'Descargado'),
    ]

    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey('authentication.Usuarios', models.CASCADE, related_name='reportes_generados')
    
    # Información del reporte
    titulo = models.CharField(max_length=255, help_text="Título personalizado del reporte")
    tipo_reporte = models.CharField(max_length=50, choices=TIPO_REPORTE_CHOICES, default='ventas')
    formato = models.CharField(max_length=10, choices=FORMATO_CHOICES, default='pdf')
    
    # Filtros aplicados (JSON)
    filtros = models.JSONField(default=dict, blank=True, help_text="Filtros aplicados al generar reporte")
    
    # Datos del reporte (JSON)
    datos_reporte = models.JSONField(default=dict, blank=True, help_text="Datos del reporte en formato JSON")
    
    # Resumen (AI-Generated)
    resumen_texto = models.TextField(blank=True, null=True, help_text="Resumen en texto del reporte (IA)")
    resumen_voz = models.FileField(
        upload_to='reportes/audio/', 
        blank=True, 
        null=True,
        help_text="Resumen de audio del reporte (TTS)"
    )
    
    # Archivos generados
    archivo_pdf = models.FileField(upload_to='reportes/pdf/', blank=True, null=True)
    archivo_excel = models.FileField(upload_to='reportes/excel/', blank=True, null=True)
    archivo_csv = models.FileField(upload_to='reportes/csv/', blank=True, null=True)
    
    # Estado y control
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='generando')
    error_mensaje = models.TextField(blank=True, null=True)
    
    # Metadatos
    total_registros = models.IntegerField(default=0, help_text="Total de registros en el reporte")
    tiempo_generacion = models.FloatField(default=0, help_text="Tiempo en segundos para generar el reporte")
    
    # Tracking
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_ultimaDescarga = models.DateTimeField(blank=True, null=True)
    descargas = models.IntegerField(default=0, help_text="Número de descargas del reporte")
    
    class Meta:
        managed = True
        db_table = 'reportes'
        ordering = ['-fecha_generacion']
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        indexes = [
            models.Index(fields=['usuario', '-fecha_generacion']),
            models.Index(fields=['tipo_reporte', 'estado']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.usuario.nombre if hasattr(self.usuario, 'nombre') else self.usuario} ({self.estado})"
    
    def marcar_completado(self):
        """Marca el reporte como completado"""
        self.estado = 'completado'
        self.save()
    
    def marcar_descargado(self):
        """Marca el reporte como descargado"""
        self.estado = 'descargado'
        self.descargas += 1
        self.fecha_ultimaDescarga = timezone.now()
        self.save()
    
    def registrar_error(self, error_msg):
        """Registra error en generación"""
        self.estado = 'error'
        self.error_mensaje = error_msg
        self.save()
    
    def get_archivo_por_formato(self):
        """Retorna el archivo según el formato especificado"""
        if self.formato == 'pdf':
            return self.archivo_pdf
        elif self.formato == 'excel':
            return self.archivo_excel
        elif self.formato == 'csv':
            return self.archivo_csv
        return None


# ============================================================================
# CU24: Gestionar Prompts Frecuentes de Reportes
# ============================================================================

class PromptFrecuente(models.Model):
    """
    CU24: Almacena prompts frecuentes para generar reportes rápidamente
    Permite guardar configuraciones de reporte usadas frecuentemente
    """
    CATEGORIA_CHOICES = [
        ('ventas', 'Ventas'),
        ('productos', 'Productos'),
        ('clientes', 'Clientes'),
        ('estadisticas', 'Estadísticas'),
        ('analisis', 'Análisis'),
        ('prediccion', 'Predicción'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey('authentication.Usuarios', models.CASCADE, related_name='prompts_frecuentes')
    
    # Información del prompt
    nombre = models.CharField(max_length=255, help_text="Nombre del prompt frecuente")
    descripcion = models.TextField(blank=True, help_text="Descripción de qué hace este prompt")
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='ventas')
    
    # Configuración del reporte
    tipo_reporte = models.CharField(max_length=50, choices=Reporte.TIPO_REPORTE_CHOICES)
    formato = models.CharField(max_length=10, choices=Reporte.FORMATO_CHOICES, default='pdf')
    filtros = models.JSONField(default=dict, help_text="Filtros predefinidos")
    opciones = models.JSONField(default=dict, blank=True, help_text="Opciones adicionales (incluir_voz, agrupar_por, etc)")
    
    # Uso
    veces_usado = models.IntegerField(default=0, help_text="Cantidad de veces utilizado")
    ultima_utilizacion = models.DateTimeField(blank=True, null=True)
    
    # Estado
    activo = models.BooleanField(default=True)
    favorito = models.BooleanField(default=False)
    
    class Meta:
        managed = True
        db_table = 'prompts_frecuentes'
        ordering = ['-favorito', '-veces_usado', '-ultima_utilizacion']
        verbose_name = 'Prompt Frecuente'
        verbose_name_plural = 'Prompts Frecuentes'
        indexes = [
            models.Index(fields=['usuario', 'activo']),
            models.Index(fields=['categoria']),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.usuario.nombre if hasattr(self.usuario, 'nombre') else self.usuario}"
    
    def registrar_uso(self):
        """Registra que se utilizó este prompt"""
        self.veces_usado += 1
        self.ultima_utilizacion = timezone.now()
        self.save()


# ============================================================================
# CU25, CU26: Predicciones de Ventas y Modelo IA
# ============================================================================

class ModeloIA(models.Model):
    """
    CU26: Almacena información del modelo de IA entrenado para predicciones
    Permite gestionar múltiples versiones de modelos
    """
    ESTADO_CHOICES = [
        ('entrenando', 'Entrenando'),
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('error', 'Error'),
        ('deprecado', 'Deprecado'),
    ]
    
    ALGORITMO_CHOICES = [
        ('linear_regression', 'Regresión Lineal'),
        ('arima', 'ARIMA'),
        ('exponential_smoothing', 'Suavización Exponencial'),
        ('prophet', 'Prophet'),
        ('random_forest', 'Random Forest'),
        ('neural_network', 'Red Neuronal'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255, help_text="Nombre del modelo")
    descripcion = models.TextField(blank=True)
    
    # Configuración
    algoritmo = models.CharField(max_length=50, choices=ALGORITMO_CHOICES, default='linear_regression')
    variable_objetivo = models.CharField(
        max_length=50, 
        choices=[('ventas', 'Ventas'), ('cantidad_transacciones', 'Cantidad de Transacciones')],
        default='ventas'
    )
    
    # Estado de entrenamiento
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='inactivo')
    
    # Datos de entrenamiento
    fecha_entrenamiento = models.DateTimeField(blank=True, null=True, help_text="Cuándo se entrenó el modelo")
    datos_entrenamiento = models.IntegerField(default=0, help_text="Cantidad de registros usados para entrenar")
    periodo_entrenamiento = models.CharField(
        max_length=20,
        choices=[('30d', 'Últimos 30 días'), ('90d', 'Últimos 90 días'), ('180d', 'Últimos 180 días'), ('1y', 'Último año')],
        default='90d'
    )
    
    # Métricas del modelo
    precision = models.FloatField(default=0.0, help_text="Precisión del modelo (0-1)")
    mae = models.FloatField(default=0.0, help_text="Mean Absolute Error")
    rmse = models.FloatField(default=0.0, help_text="Root Mean Squared Error")
    r_squared = models.FloatField(default=0.0, help_text="Coeficiente de determinación (R²)")
    
    # Archivo del modelo
    archivo_modelo = models.FileField(
        upload_to='modelos_ia/',
        blank=True,
        null=True,
        help_text="Archivo pickle o joblib del modelo"
    )
    
    # Configuración
    parametros = models.JSONField(default=dict, blank=True, help_text="Parámetros del modelo")
    error_mensaje = models.TextField(blank=True, null=True)
    
    # Usuario responsable
    creado_por = models.ForeignKey('authentication.Usuarios', models.SET_NULL, null=True, related_name='modelos_ia_creados')
    
    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = True
        db_table = 'modelos_ia'
        ordering = ['-fecha_entrenamiento']
        verbose_name = 'Modelo IA'
        verbose_name_plural = 'Modelos IA'
    
    def __str__(self):
        return f"{self.nombre} - {self.get_estado_display()}"
    
    def es_activo(self):
        """Verifica si el modelo está activo"""
        return self.estado == 'activo'


class Prediccion(models.Model):
    """
    CU25: Almacena predicciones generadas por el modelo de IA
    """
    TIPO_PREDICCION_CHOICES = [
        ('diaria', 'Predicción Diaria'),
        ('semanal', 'Predicción Semanal'),
        ('mensual', 'Predicción Mensual'),
        ('trimestral', 'Predicción Trimestral'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    modelo = models.ForeignKey(ModeloIA, models.CASCADE, related_name='predicciones')
    
    # Información de la predicción
    tipo = models.CharField(max_length=50, choices=TIPO_PREDICCION_CHOICES, default='diaria')
    fecha_prediccion = models.DateTimeField(auto_now_add=True, help_text="Cuándo se generó la predicción")
    fecha_inicio_periodo = models.DateField(help_text="Fecha de inicio del período predicho")
    fecha_fin_periodo = models.DateField(help_text="Fecha de fin del período predicho")
    
    # Valor predicho
    valor_predicho = models.DecimalField(max_digits=15, decimal_places=2, help_text="Valor predicho")
    intervalo_confianza_inferior = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True,
        help_text="Límite inferior del intervalo de confianza"
    )
    intervalo_confianza_superior = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True,
        help_text="Límite superior del intervalo de confianza"
    )
    
    # Valor real (si se ha completado el período)
    valor_real = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True,
        help_text="Valor real del período (cuando se complete)"
    )
    error_prediccion = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True,
        help_text="Error de predicción (real - predicho)"
    )
    
    # Datos adicionales
    variables_utilizadas = models.JSONField(default=dict, blank=True)
    datos_complementarios = models.JSONField(default=dict, blank=True)
    
    class Meta:
        managed = True
        db_table = 'predicciones'
        ordering = ['-fecha_prediccion']
        verbose_name = 'Predicción'
        verbose_name_plural = 'Predicciones'
        indexes = [
            models.Index(fields=['modelo', '-fecha_prediccion']),
            models.Index(fields=['fecha_inicio_periodo', 'fecha_fin_periodo']),
        ]
    
    def __str__(self):
        return f"Predicción {self.tipo} - {self.fecha_inicio_periodo} a {self.fecha_fin_periodo}"
    
    def calcular_error(self):
        """Calcula el error si ya se conoce el valor real"""
        if self.valor_real is not None:
            self.error_prediccion = self.valor_real - self.valor_predicho
            self.save()
            return self.error_prediccion
        return None