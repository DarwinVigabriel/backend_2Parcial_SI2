from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.utils.html import format_html
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('subtotal_display',)
    fields = ('producto', 'quantity', 'price', 'subtotal_display')
    
    def subtotal_display(self, obj):
        if obj.pk:
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
        return f"${obj.subtotal:.2f}"
    subtotal_display.short_description = 'Subtotal'
