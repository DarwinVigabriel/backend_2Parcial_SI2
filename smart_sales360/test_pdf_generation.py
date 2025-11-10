#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'smart_sales360'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_sales360.settings')
django.setup()

from apps.sales.models import Venta

# Obtener la primera venta
venta = Venta.objects.first()

if not venta:
    print("❌ No hay ventas en la base de datos")
    sys.exit(1)

print(f"✅ Venta encontrada: {venta.codigo_venta}")

try:
    # Generar PDF
    pdf_buffer = venta.generar_comprobante_pdf()
    
    # Guardar PDF en archivo temporal
    filename = venta.obtener_nombre_archivo_pdf()
    with open(f"test_{filename}", 'wb') as f:
        f.write(pdf_buffer.read())
    
    print(f"✅ PDF generado exitosamente: test_{filename}")
    print(f"📄 Archivo guardado en: {os.path.abspath(f'test_{filename}')}")
    
except Exception as e:
    print(f"❌ Error al generar PDF: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Probar la estadística
print("\n" + "="*50)
print("Probando módulo de estadísticas...")
print("="*50)

try:
    from apps.sales.estadisticas import EstadisticasVentas
    
    stats = EstadisticasVentas()
    estadisticas = stats.obtener_estadisticas_completas()
    
    print(f"✅ Estadísticas calculadas exitosamente")
    print(f"   Total vendido: ${estadisticas['resumen']['total_vendido']:.2f}")
    print(f"   Cantidad de ventas: {estadisticas['resumen']['cantidad_ventas']}")
    print(f"   Promedio por venta: ${estadisticas['resumen']['promedio_por_venta']:.2f}")
    
except Exception as e:
    print(f"❌ Error al calcular estadísticas: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
print("="*50)
