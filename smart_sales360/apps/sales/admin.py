from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum
from .models import Cart, CartItem, Venta, VentaDetalle, Pago, NotificacionPush, Reporte, PromptFrecuente, ModeloIA, Prediccion


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('subtotal_display',)
    fields = ('producto', 'quantity', 'price', 'subtotal_display')
    
    def subtotal_display(self, obj):
        if obj.pk and obj.subtotal is not None:
            return f"${obj.subtotal:.2f}"
        return "-"
    subtotal_display.short_description = 'Subtotal'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'cliente', 'status', 'total', 'items_count', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at', 'total')
    search_fields = ('id', 'usuario__username', 'cliente__nombre_completo')
    inlines = [CartItemInline]
    actions = ['mark_as_completed', 'mark_as_cancelled']
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} carritos marcados como completados.')
    mark_as_completed.short_description = 'Marcar como completado'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} carritos marcados como cancelados.')
    mark_as_cancelled.short_description = 'Marcar como cancelado'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('test-cart/', self.admin_site.admin_view(self.test_cart_view), name='sales_cart_test'),
        ]
        return custom_urls + urls
    
    def test_cart_view(self, request):
        """Vista para probar el carrito con texto y voz"""
        context = {
            **self.admin_site.each_context(request),
            'title': 'Probar Carrito de Compra - Texto y Voz',
            'opts': self.model._meta,
        }
        return render(request, 'admin/sales/cart_test.html', context)
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['test_cart_url'] = 'test-cart/'
        return super().changelist_view(request, extra_context)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'producto', 'quantity', 'price', 'subtotal_display', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('producto__nombre', 'cart__id')
    readonly_fields = ('created_at', 'subtotal_display')
    
    def subtotal_display(self, obj):
        if obj.subtotal is None:
            return "$0.00"
        return f"${obj.subtotal:.2f}"
    subtotal_display.short_description = 'Subtotal'


# ============================================================================
# CU12: Registrar Venta - Admin
# ============================================================================

class VentaDetalleInline(admin.TabularInline):
    model = VentaDetalle
    extra = 0
    readonly_fields = ('subtotal', 'producto_nombre_display', 'producto_sku_display')
    fields = ('producto', 'producto_nombre_display', 'producto_sku_display', 'cantidad', 'precio_unitario', 'descuento_unitario', 'subtotal')
    
    def producto_nombre_display(self, obj):
        if obj.pk and obj.producto:
            return obj.producto.nombre
        return "-"
    producto_nombre_display.short_description = 'Nombre Producto'
    
    def producto_sku_display(self, obj):
        if obj.pk and obj.producto:
            return obj.producto.sku
        return "-"
    producto_sku_display.short_description = 'SKU'
    
    def has_add_permission(self, request, obj=None):
        # No permitir agregar detalles después de crear la venta
        if obj and obj.pk:
            return False
        return True
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar detalles después de crear la venta
        if obj and obj.pk:
            return False
        return True


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    readonly_fields = ('numero_transaccion', 'estado', 'fecha_pago', 'fecha_procesamiento')
    fields = ('metodo_pago', 'monto', 'estado', 'numero_transaccion', 'fecha_pago')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_venta', 'cliente_nombre', 'usuario_nombre', 
        'total_display', 'estado_badge', 'tipo_entrega_badge', 'fecha_venta'
    )
    list_filter = ('estado', 'tipo_entrega', 'fecha_venta', 'created_at')
    search_fields = ('codigo_venta', 'cliente__nombre_completo', 'usuario__nombre')
    readonly_fields = (
        'id', 'codigo_venta', 'created_at', 'updated_at', 
        'subtotal_display', 'descuento_display', 'iva_display', 'total_display'
    )
    inlines = [VentaDetalleInline, PagoInline]
    actions = ['cancelar_ventas', 'exportar_ventas', 'descargar_comprobante_pdf']
    date_hierarchy = 'fecha_venta'
    
    fieldsets = (
        ('Información General', {
            'fields': ('codigo_venta', 'cliente', 'usuario', 'tipo_entrega', 'estado')
        }),
        ('Montos', {
            'fields': ('subtotal_display', 'descuento_display', 'iva_display', 'total_display')
        }),
        ('Pago', {
            'fields': ('metodo_pago', 'transaccion_id')
        }),
        ('Información Adicional', {
            'fields': ('notas', 'direccion_entrega', 'fecha_venta')
        }),
        ('Fechas de Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cliente_nombre(self, obj):
        return obj.cliente.nombre_completo if obj.cliente else '-'
    cliente_nombre.short_description = 'Cliente'
    
    def usuario_nombre(self, obj):
        return obj.usuario.nombre if obj.usuario else '-'
    usuario_nombre.short_description = 'Vendedor'
    
    def total_display(self, obj):
        if obj.total is None:
            return format_html('<strong>$0.00</strong>')
        return format_html('<strong>${}</strong>', f'{obj.total:.2f}')
    total_display.short_description = 'Total'
    
    def subtotal_display(self, obj):
        if obj.subtotal is None:
            return "$0.00"
        return f"${obj.subtotal:.2f}"
    subtotal_display.short_description = 'Subtotal'
    
    def descuento_display(self, obj):
        if obj.descuento is None:
            return "$0.00"
        return f"${obj.descuento:.2f}"
    descuento_display.short_description = 'Descuento'
    
    def iva_display(self, obj):
        if obj.iva is None:
            return "$0.00"
        return f"${obj.iva:.2f}"
    iva_display.short_description = 'IVA'
    
    def estado_badge(self, obj):
        colors = {
            'pendiente': '#ffc107',
            'pagada': '#28a745',
            'cancelada': '#dc3545',
            'reembolsada': '#6c757d'
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def tipo_entrega_badge(self, obj):
        colors = {
            'local': '#17a2b8',
            'domicilio': '#007bff',
            'express': '#dc3545'
        }
        color = colors.get(obj.tipo_entrega, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_tipo_entrega_display()
        )
    tipo_entrega_badge.short_description = 'Tipo Entrega'
    
    def cancelar_ventas(self, request, queryset):
        """Cancelar ventas seleccionadas"""
        count = 0
        errors = []
        
        for venta in queryset:
            if venta.estado == 'cancelada':
                errors.append(f"{venta.numero_venta} ya está cancelada")
            elif venta.estado == 'pagada':
                errors.append(f"{venta.numero_venta} está pagada, use reembolso")
            else:
                try:
                    with transaction.atomic():
                        # Revertir stock
                        for detalle in venta.detalles.all():
                            producto = detalle.producto
                            if producto.stock_actual is not None:
                                producto.stock_actual += detalle.cantidad
                                producto.save()
                        
                        venta.estado = 'cancelada'
                        venta.save()
                        count += 1
                except Exception as e:
                    errors.append(f"Error en {venta.numero_venta}: {str(e)}")
        
        if count:
            self.message_user(request, f'{count} venta(s) cancelada(s) exitosamente.', messages.SUCCESS)
        
        for error in errors:
            self.message_user(request, error, messages.WARNING)
    
    cancelar_ventas.short_description = 'Cancelar ventas seleccionadas'
    
    def exportar_ventas(self, request, queryset):
        """Exportar ventas a CSV"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="ventas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Número', 'Cliente', 'Vendedor', 'Subtotal', 'Descuento', 
            'IVA', 'Total', 'Estado', 'Tipo Entrega', 'Fecha'
        ])
        
        for venta in queryset:
            writer.writerow([
                venta.codigo_venta,
                venta.cliente.nombre_completo if venta.cliente else 'N/A',
                venta.usuario.nombre,
                venta.subtotal,
                venta.descuento,
                venta.iva,
                venta.total,
                venta.get_estado_display(),
                venta.get_tipo_entrega_display(),
                venta.fecha_venta.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    
    exportar_ventas.short_description = 'Exportar a CSV'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('crear-desde-carrito/', self.admin_site.admin_view(self.crear_desde_carrito_view), 
                 name='sales_venta_crear_desde_carrito'),
        ]
        return custom_urls + urls
    
    def crear_desde_carrito_view(self, request):
        """Vista para crear venta desde un carrito"""
        if request.method == 'POST':
            cart_id = request.POST.get('cart_id')
            cliente_id = request.POST.get('cliente_id')
            descuento = request.POST.get('descuento', 0)
            impuesto_porcentaje = request.POST.get('impuesto_porcentaje', 0)
            
            try:
                cart = Cart.objects.get(id=cart_id)
                from apps.clients.models import Clientes
                cliente = Clientes.objects.get(id=cliente_id)
                
                # Calcular totales
                subtotal = sum(item.subtotal for item in cart.items.all())
                descuento = float(descuento)
                impuesto_porcentaje = float(impuesto_porcentaje)
                
                subtotal_con_descuento = subtotal - descuento
                iva = (subtotal_con_descuento * impuesto_porcentaje) / 100
                total = subtotal_con_descuento + iva
                
                with transaction.atomic():
                    # Crear venta
                    venta = Venta.objects.create(
                        cliente=cliente,
                        usuario=request.user,
                        subtotal=subtotal,
                        descuento=descuento,
                        iva=iva,
                        total=total,
                        tipo_entrega='local',
                        estado='pendiente'
                    )
                    
                    # Crear detalles
                    for item in cart.items.all():
                        VentaDetalle.objects.create(
                            venta=venta,
                            producto=item.producto,
                            cantidad=item.quantity,
                            precio_unitario=item.price,
                            descuento_unitario=0
                        )
                        
                        # Actualizar stock
                        producto = item.producto
                        if producto.stock_actual is not None:
                            producto.stock_actual -= item.quantity
                            producto.save()
                    
                    # Cerrar carrito
                    cart.status = 'completed'
                    cart.save()
                
                messages.success(request, f'Venta {venta.codigo_venta} creada exitosamente')
                return redirect('admin:sales_venta_change', venta.id)
                
            except Exception as e:
                messages.error(request, f'Error al crear venta: {str(e)}')
        
        # GET: mostrar formulario
        from apps.clients.models import Clientes
        carritos = Cart.objects.filter(status='open')
        clientes = Clientes.objects.filter(activo=True)
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Crear Venta desde Carrito',
            'carritos': carritos,
            'clientes': clientes,
            'opts': self.model._meta,
        }
        return render(request, 'admin/sales/crear_venta_desde_carrito.html', context)
    
    # CU14: Acción para descargar comprobante PDF
    def descargar_comprobante_pdf(self, request, queryset):
        """Acción para descargar comprobante de venta en PDF"""
        if queryset.count() == 1:
            venta = queryset.first()
            
            try:
                # Generar PDF
                pdf_buffer = venta.generar_comprobante_pdf()
                
                # Preparar respuesta
                response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{venta.obtener_nombre_archivo_pdf()}"'
                return response
            except Exception as e:
                messages.error(request, f'Error al generar comprobante: {str(e)}')
        else:
            messages.error(request, 'Selecciona una sola venta para descargar el comprobante')
    
    descargar_comprobante_pdf.short_description = '📄 Descargar Comprobante PDF'
    
    # CU15: Vista personalizada para listar con filtros
    def changelist_view(self, request, extra_context=None):
        """
        Agrega información de filtros disponibles
        """
        from .estadisticas import EstadisticasVentas
        
        extra_context = extra_context or {}
        
        # Calcular estadísticas rápidas
        stats = EstadisticasVentas()
        resumen = stats.obtener_resumen()
        
        extra_context['resumen_ventas'] = resumen
        extra_context['show_dashboard_button'] = True
        
        return super().changelist_view(request, extra_context=extra_context)
    
    # CU16: Acción para ver dashboard
    def dashboard_ventas(self, request):
        """Vista personalizada para mostrar dashboard de ventas"""
        from .estadisticas import EstadisticasVentas
        from django.utils.dateparse import parse_date
        
        # Obtener parámetros de filtro
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        cliente_id = request.GET.get('cliente_id')
        estado = request.GET.get('estado')
        
        fecha_inicio = parse_date(fecha_inicio_str) if fecha_inicio_str else None
        fecha_fin = parse_date(fecha_fin_str) if fecha_fin_str else None
        
        # Calcular estadísticas
        stats_obj = EstadisticasVentas(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            cliente_id=cliente_id if cliente_id else None,
            estado=estado if estado else None
        )
        
        estadisticas = stats_obj.obtener_estadisticas_completas()
        
        from apps.clients.models import Clientes
        clientes = Clientes.objects.filter(activo=True)
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Dashboard de Ventas',
            'estadisticas': estadisticas,
            'clientes': clientes,
            'opts': self.model._meta,
            'fecha_inicio': fecha_inicio_str,
            'fecha_fin': fecha_fin_str,
            'cliente_id': cliente_id,
            'estado': estado,
        }
        
        return render(request, 'admin/sales/dashboard_ventas.html', context)
    
    def get_urls(self):
        """Agrega URLs personalizadas"""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_ventas), name='sales_venta_dashboard'),
        ]
        return custom_urls + urls


@admin.register(VentaDetalle)
class VentaDetalleAdmin(admin.ModelAdmin):
    list_display = ('id', 'venta_codigo', 'producto_nombre_display', 'cantidad', 'precio_unitario', 'subtotal_display')
    list_filter = ('created_at',)
    search_fields = ('venta__codigo_venta', 'producto__nombre', 'producto__sku')
    readonly_fields = ('subtotal', 'created_at')
    
    def venta_codigo(self, obj):
        return obj.venta.codigo_venta
    venta_codigo.short_description = 'Venta'
    
    def producto_nombre_display(self, obj):
        return obj.producto.nombre
    producto_nombre_display.short_description = 'Producto'
    
    def subtotal_display(self, obj):
        if obj.subtotal is None:
            return "$0.00"
        return f"${obj.subtotal:.2f}"
    subtotal_display.short_description = 'Subtotal'
    
    def has_add_permission(self, request):
        # Los detalles solo se crean junto con la venta
        return False


# ============================================================================
# CU13: Procesar Pago en Línea - Admin
# ============================================================================

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_transaccion', 'venta_numero', 'monto_display', 
        'metodo_pago_badge', 'estado_badge', 'fecha_pago'
    )
    list_filter = ('metodo_pago', 'estado', 'fecha_pago', 'created_at')
    search_fields = ('numero_transaccion', 'numero_autorizacion', 'venta__numero_venta')
    readonly_fields = (
        'id', 'numero_transaccion', 'numero_autorizacion', 
        'fecha_procesamiento', 'created_at', 'updated_at', 'qr_imagen_preview'
    )
    actions = ['procesar_pagos', 'reembolsar_pagos']
    date_hierarchy = 'fecha_pago'
    
    fieldsets = (
        ('Información General', {
            'fields': ('numero_transaccion', 'venta', 'monto', 'metodo_pago', 'estado')
        }),
        ('Información de Tarjeta', {
            'fields': ('tarjeta_ultimos_digitos', 'tarjeta_tipo', 'numero_autorizacion'),
            'classes': ('collapse',)
        }),
        ('Información de QR', {
            'fields': ('qr_codigo', 'qr_imagen_url', 'qr_imagen_preview'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_pago', 'fecha_procesamiento')
        }),
        ('Adicional', {
            'fields': ('notas',)
        }),
        ('Fechas de Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def venta_numero(self, obj):
        return obj.venta.codigo_venta
    venta_numero.short_description = 'Venta'
    
    def monto_display(self, obj):
        if obj.monto is None:
            return format_html('<strong>$0.00</strong>')
        return format_html('<strong>${}</strong>', f'{obj.monto:.2f}')
    monto_display.short_description = 'Monto'
    
    def metodo_pago_badge(self, obj):
        colors = {
            'efectivo': '#28a745',
            'tarjeta_credito': '#007bff',
            'tarjeta_debito': '#17a2b8',
            'transferencia': '#6f42c1',
            'qr': '#fd7e14',
            'paypal': '#0070ba',
            'otro': '#6c757d'
        }
        color = colors.get(obj.metodo_pago, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_metodo_pago_display()
        )
    metodo_pago_badge.short_description = 'Método de Pago'
    
    def estado_badge(self, obj):
        colors = {
            'pendiente': '#ffc107',
            'procesando': '#17a2b8',
            'completado': '#28a745',
            'fallido': '#dc3545',
            'reembolsado': '#6c757d'
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def qr_imagen_preview(self, obj):
        if obj.qr_imagen_url:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" /><br><a href="{}" target="_blank">Ver imagen completa</a>',
                obj.qr_imagen_url, obj.qr_imagen_url
            )
        return '-'
    qr_imagen_preview.short_description = 'Vista Previa QR'
    
    def procesar_pagos(self, request, queryset):
        """Procesar pagos pendientes"""
        count = 0
        errors = []
        
        for pago in queryset:
            if pago.estado != 'pendiente':
                errors.append(f"{pago.numero_transaccion} no está pendiente")
            else:
                try:
                    if pago.procesar_pago():
                        count += 1
                    else:
                        errors.append(f"{pago.numero_transaccion} falló al procesar")
                except Exception as e:
                    errors.append(f"Error en {pago.numero_transaccion}: {str(e)}")
        
        if count:
            self.message_user(request, f'{count} pago(s) procesado(s) exitosamente.', messages.SUCCESS)
        
        for error in errors:
            self.message_user(request, error, messages.WARNING)
    
    procesar_pagos.short_description = 'Procesar pagos pendientes'
    
    def reembolsar_pagos(self, request, queryset):
        """Reembolsar pagos completados"""
        count = 0
        errors = []
        
        for pago in queryset:
            if pago.estado != 'completado':
                errors.append(f"{pago.numero_transaccion} no está completado")
            else:
                try:
                    with transaction.atomic():
                        pago.estado = 'reembolsado'
                        pago.save()
                        
                        if pago.venta:
                            pago.venta.estado = 'reembolsada'
                            pago.venta.save()
                            
                            # Revertir stock
                            for detalle in pago.venta.detalles.all():
                                producto = detalle.producto
                                if producto.stock_actual is not None:
                                    producto.stock_actual += detalle.cantidad
                                    producto.save()
                        
                        count += 1
                except Exception as e:
                    errors.append(f"Error en {pago.numero_transaccion}: {str(e)}")
        
        if count:
            self.message_user(request, f'{count} pago(s) reembolsado(s) exitosamente.', messages.SUCCESS)
        
        for error in errors:
            self.message_user(request, error, messages.WARNING)
    
    reembolsar_pagos.short_description = 'Reembolsar pagos'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('procesar-pago/', self.admin_site.admin_view(self.procesar_pago_view), 
                 name='sales_pago_procesar'),
            path('generar-qr/', self.admin_site.admin_view(self.generar_qr_view), 
                 name='sales_pago_generar_qr'),
        ]
        return custom_urls + urls
    
    def procesar_pago_view(self, request):
        """Vista para procesar un nuevo pago"""
        if request.method == 'POST':
            venta_id = request.POST.get('venta_id')
            monto = request.POST.get('monto')
            metodo_pago = request.POST.get('metodo_pago')
            
            try:
                venta = Venta.objects.get(id=venta_id)
                
                # Crear pago
                pago = Pago.objects.create(
                    venta=venta,
                    monto=monto,
                    metodo_pago=metodo_pago,
                    estado='pendiente'
                )
                
                # Procesar
                if pago.procesar_pago():
                    messages.success(request, f'Pago {pago.numero_transaccion} procesado exitosamente')
                else:
                    messages.error(request, f'Pago {pago.numero_transaccion} fue rechazado')
                
                return redirect('admin:sales_pago_change', pago.id)
                
            except Exception as e:
                messages.error(request, f'Error al procesar pago: {str(e)}')
        
        # GET: mostrar formulario
        ventas = Venta.objects.filter(estado='pendiente')
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Procesar Pago',
            'ventas': ventas,
            'metodos_pago': Pago.METODO_PAGO_CHOICES,
            'opts': self.model._meta,
        }
        return render(request, 'admin/sales/procesar_pago.html', context)
    
    def generar_qr_view(self, request):
        """Vista para generar código QR de pago"""
        if request.method == 'POST':
            venta_id = request.POST.get('venta_id')
            
            try:
                import random
                venta = Venta.objects.get(id=venta_id)
                
                # Generar código QR
                qr_codigo = f'QR-{venta.numero_venta}-{random.randint(100000, 999999)}'
                qr_imagen_url = f'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_codigo}'
                
                # Crear pago con QR
                pago = Pago.objects.create(
                    venta=venta,
                    monto=venta.total,
                    metodo_pago='qr',
                    estado='pendiente',
                    qr_codigo=qr_codigo,
                    qr_imagen_url=qr_imagen_url
                )
                
                messages.success(request, f'Código QR generado: {qr_codigo}')
                return redirect('admin:sales_pago_change', pago.id)
                
            except Exception as e:
                messages.error(request, f'Error al generar QR: {str(e)}')
        
        # GET: mostrar formulario
        ventas = Venta.objects.filter(estado='pendiente')
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Generar Código QR',
            'ventas': ventas,
            'opts': self.model._meta,
        }
        return render(request, 'admin/sales/generar_qr.html', context)


# CU20: Administración de Notificaciones Push
@admin.register(NotificacionPush)
class NotificacionPushAdmin(admin.ModelAdmin):
    """Admin para gestionar notificaciones push"""
    list_display = ('titulo', 'usuario_link', 'tipo', 'estado', 'intentos', 'created_at')
    list_filter = ('tipo', 'estado', 'created_at', 'fecha_envio')
    search_fields = ('titulo', 'mensaje', 'usuario__nombre', 'cliente__nombre_completo')
    readonly_fields = ('id', 'fecha_envio', 'fecha_entrega', 'intentos', 'error_mensaje', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Destinatario', {
            'fields': ('usuario', 'cliente', 'venta')
        }),
        ('Contenido', {
            'fields': ('titulo', 'mensaje', 'tipo', 'datos_adicionales')
        }),
        ('Estado de Entrega', {
            'fields': ('estado', 'fecha_envio', 'fecha_entrega', 'intentos', 'error_mensaje')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_como_enviada', 'marcar_como_entregada', 'reintentar_envio']
    
    def usuario_link(self, obj):
        if obj.usuario:
            return obj.usuario.nombre if hasattr(obj.usuario, 'nombre') else str(obj.usuario)
        return '-'
    usuario_link.short_description = 'Usuario'
    
    def marcar_como_enviada(self, request, queryset):
        updated = queryset.update(estado='enviada')
        messages.info(request, f'{updated} notificación(es) marcada(s) como enviada(s).')
    marcar_como_enviada.short_description = '📤 Marcar como enviada'
    
    def marcar_como_entregada(self, request, queryset):
        updated = 0
        for notif in queryset:
            notif.marcar_entregada()
            updated += 1
        messages.success(request, f'{updated} notificación(es) marcada(s) como entregada(s).')
    marcar_como_entregada.short_description = '✓ Marcar como entregada'
    
    def reintentar_envio(self, request, queryset):
        updated = queryset.filter(estado='fallida').update(estado='pendiente', intentos=0)
        messages.info(request, f'{updated} notificación(es) preparada(s) para reintentar.')
    reintentar_envio.short_description = '🔄 Reintentar envío'


# ============================================================================
# CU21, CU22, CU23: Administración de Reportes Dinámicos
# ============================================================================

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    """Admin para gestionar Reportes Dinámicos (CU21, CU22, CU23)"""
    list_display = (
        'titulo', 'usuario_nombre', 'tipo_reporte_display', 'formato_display',
        'estado_badge', 'total_registros', 'descargas', 'fecha_generacion'
    )
    list_filter = ('tipo_reporte', 'formato', 'estado', 'fecha_generacion')
    search_fields = ('titulo', 'usuario__nombre', 'resumen_texto')
    readonly_fields = (
        'id', 'usuario', 'estado', 'total_registros', 'tiempo_generacion',
        'fecha_generacion', 'fecha_ultimaDescarga', 'descargas',
        'datos_reporte_preview', 'archivo_pdf_preview', 'archivo_excel_preview',
        'resumen_voz_preview', 'error_mensaje'
    )
    
    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'usuario', 'tipo_reporte', 'formato', 'estado')
        }),
        ('Configuración', {
            'fields': ('filtros',)
        }),
        ('Contenido', {
            'fields': ('resumen_texto', 'resumen_voz_preview'),
            'classes': ('collapse',)
        }),
        ('Datos del Reporte', {
            'fields': ('datos_reporte_preview', 'total_registros'),
            'classes': ('collapse',)
        }),
        ('Archivos Generados', {
            'fields': ('archivo_pdf_preview', 'archivo_excel_preview', 'archivo_csv'),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('tiempo_generacion', 'descargas', 'fecha_ultimaDescarga')
        }),
        ('Errores', {
            'fields': ('error_mensaje',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('fecha_generacion',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['descargar_pdf', 'descargar_excel', 'generar_voz', 'regenerar_reportes']
    date_hierarchy = 'fecha_generacion'
    
    def usuario_nombre(self, obj):
        return obj.usuario.nombre if hasattr(obj.usuario, 'nombre') else str(obj.usuario)
    usuario_nombre.short_description = 'Usuario'
    
    def tipo_reporte_display(self, obj):
        return obj.get_tipo_reporte_display()
    tipo_reporte_display.short_description = 'Tipo'
    
    def formato_display(self, obj):
        return obj.get_formato_display()
    formato_display.short_description = 'Formato'
    
    def estado_badge(self, obj):
        colors = {
            'generando': '#ffc107',
            'completado': '#28a745',
            'error': '#dc3545',
            'descargado': '#17a2b8'
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def datos_reporte_preview(self, obj):
        """Vista previa de los datos del reporte en JSON"""
        if obj.datos_reporte:
            import json
            datos_str = json.dumps(obj.datos_reporte, indent=2, ensure_ascii=False)[:500]
            return format_html('<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', datos_str)
        return '-'
    datos_reporte_preview.short_description = 'Vista Previa Datos'
    
    def archivo_pdf_preview(self, obj):
        """Link para descargar PDF si existe"""
        if obj.archivo_pdf and obj.archivo_pdf.name:
            return format_html(
                '<a class="button" href="{}">📥 Descargar PDF</a>',
                obj.archivo_pdf.url
            )
        return format_html('<span style="color: gray;">No disponible</span>')
    archivo_pdf_preview.short_description = 'PDF'
    
    def archivo_excel_preview(self, obj):
        """Link para descargar Excel si existe"""
        if obj.archivo_excel and obj.archivo_excel.name:
            return format_html(
                '<a class="button" href="{}">📥 Descargar Excel</a>',
                obj.archivo_excel.url
            )
        return format_html('<span style="color: gray;">No disponible</span>')
    archivo_excel_preview.short_description = 'Excel'
    
    def resumen_voz_preview(self, obj):
        """Reproductor de audio si existe"""
        if obj.resumen_voz and obj.resumen_voz.name:
            return format_html(
                '<audio controls style="width: 100%; max-width: 300px;"><source src="{}" type="audio/mpeg">Tu navegador no soporta audio.</audio>',
                obj.resumen_voz.url
            )
        return format_html('<span style="color: gray;">No disponible</span>')
    resumen_voz_preview.short_description = 'Audio'
    
    def descargar_pdf(self, request, queryset):
        """Acción para descargar reportes en PDF"""
        count = 0
        for reporte in queryset:
            if reporte.archivo_pdf and reporte.archivo_pdf.name:
                count += 1
        
        if count:
            messages.info(request, f'{count} reporte(s) disponible(s) para descargar como PDF')
        else:
            messages.warning(request, 'Ninguno de los reportes seleccionados tiene PDF generado')
    descargar_pdf.short_description = '📥 Descargar PDF'
    
    def descargar_excel(self, request, queryset):
        """Acción para descargar reportes en Excel"""
        count = 0
        for reporte in queryset:
            if reporte.archivo_excel and reporte.archivo_excel.name:
                count += 1
        
        if count:
            messages.info(request, f'{count} reporte(s) disponible(s) para descargar como Excel')
        else:
            messages.warning(request, 'Ninguno de los reportes seleccionados tiene Excel generado')
    descargar_excel.short_description = '📊 Descargar Excel'
    
    def generar_voz(self, request, queryset):
        """Acción para generar versión de voz de reportes"""
        count = 0
        for reporte in queryset:
            if reporte.resumen_texto and not reporte.resumen_voz:
                count += 1
        
        if count:
            messages.success(request, f'{count} reporte(s) preparado(s) para generar voz')
    generar_voz.short_description = '🔊 Generar Versión de Voz'
    
    def regenerar_reportes(self, request, queryset):
        """Acción para regenerar reportes"""
        updated = 0
        for reporte in queryset:
            if reporte.estado == 'error':
                reporte.estado = 'generando'
                reporte.error_mensaje = ''
                reporte.save()
                updated += 1
        
        messages.success(request, f'{updated} reporte(s) preparado(s) para regenerar')
    regenerar_reportes.short_description = '🔄 Regenerar Reportes'
    
    def get_urls(self):
        """Agrega URLs personalizadas"""
        urls = super().get_urls()
        custom_urls = [
            path('generar-nuevo/', self.admin_site.admin_view(self.generar_nuevo_reporte_view),
                 name='sales_reporte_generar_nuevo'),
        ]
        return custom_urls + urls
    
    def generar_nuevo_reporte_view(self, request):
        """Vista para generar un nuevo reporte desde el admin"""
        if request.method == 'POST':
            titulo = request.POST.get('titulo')
            tipo_reporte = request.POST.get('tipo_reporte')
            formato = request.POST.get('formato', 'pdf')
            incluir_voz = request.POST.get('incluir_voz') == 'on'
            
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_fin = request.POST.get('fecha_fin')
            cliente_id = request.POST.get('cliente_id')
            
            try:
                # Construir filtros
                filtros = {}
                if fecha_inicio:
                    filtros['fecha_inicio'] = fecha_inicio
                if fecha_fin:
                    filtros['fecha_fin'] = fecha_fin
                if cliente_id:
                    filtros['cliente_id'] = cliente_id
                
                # Crear reporte
                reporte = Reporte.objects.create(
                    usuario=request.user.usuarios if hasattr(request.user, 'usuarios') else None,
                    titulo=titulo,
                    tipo_reporte=tipo_reporte,
                    formato=formato,
                    filtros=filtros,
                    estado='generando'
                )
                
                messages.success(request, f'Reporte "{reporte.titulo}" creado exitosamente')
                return redirect('admin:sales_reporte_change', reporte.id)
            
            except Exception as e:
                messages.error(request, f'Error al crear reporte: {str(e)}')
        
        # GET: mostrar formulario
        from apps.clients.models import Clientes
        clientes = Clientes.objects.filter(activo=True)
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Generar Nuevo Reporte',
            'tipos_reporte': Reporte.TIPO_REPORTE_CHOICES,
            'formatos': Reporte.FORMATO_CHOICES,
            'clientes': clientes,
            'opts': self.model._meta,
        }
        return render(request, 'admin/sales/generar_reporte.html', context)


# ============================================================================
# CU24: Administración de Prompts Frecuentes
# ============================================================================

@admin.register(PromptFrecuente)
class PromptFrecuenteAdmin(admin.ModelAdmin):
    """Admin para gestionar Prompts Frecuentes (CU24)"""
    list_display = (
        'nombre', 'usuario_nombre', 'categoria', 'tipo_reporte', 'formato',
        'favorito_icon', 'veces_usado', 'activo', 'ultima_utilizacion'
    )
    list_filter = ('categoria', 'tipo_reporte', 'formato', 'favorito', 'activo', 'ultima_utilizacion')
    search_fields = ('nombre', 'descripcion', 'usuario__nombre')
    readonly_fields = ('veces_usado', 'ultima_utilizacion')
    
    fieldsets = (
        ('Información', {
            'fields': ('usuario', 'nombre', 'descripcion', 'categoria')
        }),
        ('Configuración de Reporte', {
            'fields': ('tipo_reporte', 'formato', 'filtros', 'opciones')
        }),
        ('Uso', {
            'fields': ('veces_usado', 'ultima_utilizacion', 'favorito', 'activo')
        }),
    )
    
    actions = ['marcar_como_favorito', 'desmarcar_como_favorito', 'desactivar_prompts']
    
    def usuario_nombre(self, obj):
        return obj.usuario.nombre if hasattr(obj.usuario, 'nombre') else str(obj.usuario)
    usuario_nombre.short_description = 'Usuario'
    
    def favorito_icon(self, obj):
        if obj.favorito:
            return format_html('⭐ Sí')
        return format_html('☆ No')
    favorito_icon.short_description = 'Favorito'
    
    def marcar_como_favorito(self, request, queryset):
        updated = queryset.update(favorito=True)
        messages.success(request, f'{updated} prompt(s) marcado(s) como favorito')
    marcar_como_favorito.short_description = '⭐ Marcar como favorito'
    
    def desmarcar_como_favorito(self, request, queryset):
        updated = queryset.update(favorito=False)
        messages.success(request, f'{updated} prompt(s) desmarcado(s)')
    desmarcar_como_favorito.short_description = '☆ Desmarcar como favorito'
    
    def desactivar_prompts(self, request, queryset):
        updated = queryset.update(activo=False)
        messages.info(request, f'{updated} prompt(s) desactivado(s)')
    desactivar_prompts.short_description = '❌ Desactivar prompts'


# ============================================================================
# CU26: Administración de Modelos IA
# ============================================================================

@admin.register(ModeloIA)
class ModeloIAAdmin(admin.ModelAdmin):
    """Admin para gestionar Modelos IA (CU26)"""
    list_display = (
        'nombre', 'algoritmo', 'estado_badge', 'precision_display',
        'r_squared_display', 'fecha_entrenamiento', 'creado_por_nombre'
    )
    list_filter = ('estado', 'algoritmo', 'variable_objetivo', 'fecha_entrenamiento')
    search_fields = ('nombre', 'descripcion', 'creado_por__nombre')
    readonly_fields = (
        'fecha_entrenamiento', 'datos_entrenamiento', 'precision', 'mae', 'rmse',
        'r_squared', 'creado_en', 'actualizado_en', 'error_mensaje'
    )
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'descripcion', 'algoritmo', 'variable_objetivo')
        }),
        ('Estado', {
            'fields': ('estado', 'error_mensaje')
        }),
        ('Entrenamiento', {
            'fields': (
                'fecha_entrenamiento', 'datos_entrenamiento', 'periodo_entrenamiento'
            )
        }),
        ('Métricas', {
            'fields': ('precision', 'mae', 'rmse', 'r_squared')
        }),
        ('Configuración', {
            'fields': ('parametros', 'archivo_modelo'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['entrenar_modelos', 'activar_modelo', 'desactivar_modelos']
    
    def estado_badge(self, obj):
        colores = {
            'entrenando': '#ffc107',
            'activo': '#28a745',
            'inactivo': '#6c757d',
            'error': '#dc3545',
            'deprecado': '#17a2b8'
        }
        color = colores.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def precision_display(self, obj):
        if obj.precision > 0:
            return f'{obj.precision:.2%}'
        return '-'
    precision_display.short_description = 'Precisión'
    
    def r_squared_display(self, obj):
        if obj.r_squared > 0:
            return f'{obj.r_squared:.4f}'
        return '-'
    r_squared_display.short_description = 'R²'
    
    def creado_por_nombre(self, obj):
        return obj.creado_por.nombre if obj.creado_por and hasattr(obj.creado_por, 'nombre') else 'N/A'
    creado_por_nombre.short_description = 'Creado Por'
    
    def entrenar_modelos(self, request, queryset):
        updated = queryset.exclude(estado='entrenando').update(estado='entrenando')
        messages.info(request, f'{updated} modelo(s) preparado(s) para entrenar')
    entrenar_modelos.short_description = '🔄 Entrenar modelos'
    
    def activar_modelo(self, request, queryset):
        if queryset.count() == 1:
            modelo = queryset.first()
            if modelo.estado == 'activo':
                # Desactivar otros
                ModeloIA.objects.filter(estado='activo').exclude(id=modelo.id).update(estado='inactivo')
                messages.success(request, f'Modelo "{modelo.nombre}" activado')
            else:
                messages.error(request, 'El modelo debe estar en estado activo')
        else:
            messages.error(request, 'Selecciona un solo modelo para activar')
    activar_modelo.short_description = '✓ Activar modelo'
    
    def desactivar_modelos(self, request, queryset):
        updated = queryset.filter(estado='activo').update(estado='inactivo')
        messages.info(request, f'{updated} modelo(s) desactivado(s)')
    desactivar_modelos.short_description = '✕ Desactivar modelos'


# ============================================================================
# CU25: Administración de Predicciones
# ============================================================================

@admin.register(Prediccion)
class PrediccionAdmin(admin.ModelAdmin):
    """Admin para gestionar Predicciones (CU25)"""
    list_display = (
        'id', 'modelo_nombre', 'tipo', 'fecha_inicio_periodo', 'fecha_fin_periodo',
        'valor_predicho_display', 'valor_real_display', 'error_display', 'fecha_prediccion'
    )
    list_filter = ('tipo', 'modelo', 'fecha_inicio_periodo', 'fecha_prediccion')
    search_fields = ('modelo__nombre', 'variables_utilizadas')
    readonly_fields = (
        'fecha_prediccion', 'error_prediccion', 'datos_complementarios_preview'
    )
    
    fieldsets = (
        ('Información', {
            'fields': ('modelo', 'tipo', 'fecha_prediccion')
        }),
        ('Período', {
            'fields': ('fecha_inicio_periodo', 'fecha_fin_periodo')
        }),
        ('Predicción', {
            'fields': (
                'valor_predicho', 'intervalo_confianza_inferior',
                'intervalo_confianza_superior'
            )
        }),
        ('Valor Real', {
            'fields': ('valor_real', 'error_prediccion')
        }),
        ('Datos Adicionales', {
            'fields': ('variables_utilizadas', 'datos_complementarios_preview'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['registrar_valor_real']
    
    def modelo_nombre(self, obj):
        return obj.modelo.nombre
    modelo_nombre.short_description = 'Modelo'
    
    def valor_predicho_display(self, obj):
        return format_html('<strong>${:,.2f}</strong>', obj.valor_predicho)
    valor_predicho_display.short_description = 'Valor Predicho'
    
    def valor_real_display(self, obj):
        if obj.valor_real:
            return format_html('<strong>${:,.2f}</strong>', obj.valor_real)
        return format_html('<span style="color: gray;">Pendiente</span>')
    valor_real_display.short_description = 'Valor Real'
    
    def error_display(self, obj):
        if obj.error_prediccion is not None:
            error_pct = (obj.error_prediccion / obj.valor_predicho * 100) if obj.valor_predicho else 0
            color = 'green' if abs(error_pct) < 10 else 'orange' if abs(error_pct) < 20 else 'red'
            return format_html(
                '<span style="color: {};">${:,.2f} ({:.1f}%)</span>',
                color, obj.error_prediccion, error_pct
            )
        return '-'
    error_display.short_description = 'Error'
    
    def datos_complementarios_preview(self, obj):
        if obj.datos_complementarios:
            import json
            datos_str = json.dumps(obj.datos_complementarios, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', datos_str)
        return '-'
    datos_complementarios_preview.short_description = 'Datos Complementarios'
    
    def registrar_valor_real(self, request, queryset):
        """Acción para registrar valor real"""
        for prediccion in queryset:
            if prediccion.valor_real is None and prediccion.fecha_fin_periodo <= timezone.now().date():
                # Buscar venta real
                ventas = Venta.objects.filter(
                    fecha_venta__date__gte=prediccion.fecha_inicio_periodo,
                    fecha_venta__date__lte=prediccion.fecha_fin_periodo
                ).aggregate(total=Sum('total'))
                
                prediccion.valor_real = ventas['total'] or 0
                prediccion.calcular_error()
        
        messages.success(request, 'Valores reales registrados')
    registrar_valor_real.short_description = '📊 Registrar Valor Real'

