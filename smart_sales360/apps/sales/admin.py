from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from .models import Cart, CartItem, Venta, VentaDetalle, Pago, NotificacionPush


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

