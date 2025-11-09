#!/usr/bin/env python
"""
Script para crear un pago QR de prueba y verificar que se genere correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_sales360.settings')
django.setup()

from apps.sales.models import Pago, Venta
from django.utils import timezone

print("=" * 80)
print("🧪 PRUEBA DE GENERACIÓN DE QR")
print("=" * 80)

# Obtener una venta existente
print("\n📋 Buscando ventas existentes...")
ventas = Venta.objects.all()[:3]

if not ventas:
    print("❌ No hay ventas en la base de datos")
    print("   Por favor, crea una venta primero")
    sys.exit(1)

venta = ventas[0]
print(f"✅ Venta encontrada: {venta.codigo_venta} (ID: {venta.id})")
print(f"   Cliente: {venta.cliente.nombre_completo if venta.cliente else 'Sin cliente'}")
print(f"   Monto: ${venta.total}")

# Crear un nuevo pago QR
print("\n💳 Creando pago QR...")
pago = Pago.objects.create(
    venta=venta,
    monto=venta.total,
    metodo_pago='qr',
    estado='pendiente',
    notas='Pago de prueba QR'
)

print(f"✅ Pago creado (ID: {pago.id})")
print(f"   Número de transacción: {pago.numero_transaccion}")
print(f"   Estado: {pago.estado}")

# Procesar el pago (genera QR)
print("\n⚙️  Procesando pago con Stripe...")
pago.procesar_pago()

# Recargar desde BD
pago.refresh_from_db()

print(f"✅ Pago procesado")
print(f"   Estado: {pago.estado}")
print(f"   Fecha procesamiento: {pago.fecha_procesamiento}")

# Verificar QR
print("\n📱 Información del QR:")
print(f"   Código QR: {pago.qr_codigo}")
print(f"   URL Imagen: {pago.qr_imagen_url}")

if pago.qr_codigo and pago.qr_imagen_url:
    print("\n✅ ¡QR generado exitosamente!")
    print(f"\n🖼️  Abre esta URL en tu navegador para ver el código QR:")
    print(f"   {pago.qr_imagen_url}")
else:
    print("\n❌ El QR no se generó correctamente")
    print(f"   qr_codigo: {pago.qr_codigo}")
    print(f"   qr_imagen_url: {pago.qr_imagen_url}")

# Información adicional
print("\n📊 Información del Pago:")
print(f"   ID: {pago.id}")
print(f"   Venta: {pago.venta.codigo_venta}")
print(f"   Monto: ${pago.monto}")
print(f"   Método: {pago.get_metodo_pago_display()}")
print(f"   Estado: {pago.get_estado_display()}")
print(f"   Número Autorización: {pago.numero_autorizacion}")

# Actualizar venta
venta.refresh_from_db()
print(f"\n💰 Estado de la Venta después del Pago:")
print(f"   Código: {venta.codigo_venta}")
print(f"   Estado: {venta.get_estado_display()}")
print(f"   Método Pago: {venta.get_metodo_pago_display()}")

print("\n" + "=" * 80)
print("✅ PRUEBA COMPLETADA")
print("=" * 80)
