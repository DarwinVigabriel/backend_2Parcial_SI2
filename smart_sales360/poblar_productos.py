"""
Script para poblar la base de datos con productos de prueba
Ejecutar: python poblar_productos.py
"""

import sys
import os
from decimal import Decimal
from datetime import datetime

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_sales360.settings')

import django
django.setup()

from apps.products.models import Productos
from apps.categories.models import Categorias


def crear_categoria_si_no_existe(nombre, descripcion=""):
    """Crear o obtener una categoría"""
    categoria, created = Categorias.objects.get_or_create(
        nombre=nombre,
        defaults={
            'descripcion': descripcion,
            'activo': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    )
    if created:
        print(f"  ✅ Categoría creada: {nombre}")
    else:
        print(f"  📌 Categoría existente: {nombre}")
    return categoria


def crear_producto(sku, nombre, categoria, precio, stock, descripcion="", codigo_barras=None):
    """Crear o actualizar un producto"""
    producto, created = Productos.objects.update_or_create(
        sku=sku,
        defaults={
            'codigo_barras': codigo_barras or f"BAR{sku}",
            'nombre': nombre,
            'descripcion': descripcion,
            'categoria': categoria,
            'precio_venta': Decimal(str(precio)),
            'precio_compra': Decimal(str(precio * 0.6)),  # 60% del precio de venta
            'stock_actual': stock,
            'stock_minimo': 5,
            'stock_maximo': 100,
            'peso_kg': Decimal('0.5'),
            'activo': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    )
    if created:
        print(f"  ✅ Producto creado: {sku} - {nombre}")
    else:
        print(f"  🔄 Producto actualizado: {sku} - {nombre}")
    return producto


def poblar_productos():
    """Poblar la base de datos con productos de prueba"""
    print("\n" + "="*60)
    print("🛒 POBLANDO BASE DE DATOS CON PRODUCTOS DE PRUEBA")
    print("="*60)
    
    # Crear categorías
    print("\n📁 Creando categorías...")
    cat_electronica = crear_categoria_si_no_existe(
        "Electrónica",
        "Productos electrónicos y tecnología"
    )
    cat_oficina = crear_categoria_si_no_existe(
        "Oficina",
        "Artículos de oficina y papelería"
    )
    cat_hogar = crear_categoria_si_no_existe(
        "Hogar",
        "Artículos para el hogar"
    )
    cat_ropa = crear_categoria_si_no_existe(
        "Ropa",
        "Prendas de vestir"
    )
    
    # Crear productos - Electrónica
    print("\n💻 Creando productos de Electrónica...")
    productos_electronica = [
        ("LAPTOP001", "Laptop HP Pavilion 15", 12500.00, 15, "Laptop HP Pavilion 15.6 pulgadas, Intel i5, 8GB RAM, 256GB SSD"),
        ("LAPTOP002", "Laptop Dell Inspiron", 11000.00, 10, "Laptop Dell Inspiron 14, AMD Ryzen 5, 8GB RAM, 512GB SSD"),
        ("MOUSE001", "Mouse Logitech MX Master", 350.00, 50, "Mouse inalámbrico ergonómico Logitech MX Master 3"),
        ("MOUSE002", "Mouse Razer DeathAdder", 280.00, 30, "Mouse gaming Razer DeathAdder V2"),
        ("TECLADO001", "Teclado Mecánico RGB", 450.00, 25, "Teclado mecánico gaming con retroiluminación RGB"),
        ("TECLADO002", "Teclado Logitech K380", 180.00, 40, "Teclado inalámbrico compacto multi-dispositivo"),
        ("MONITOR001", "Monitor LG 24 pulgadas", 1200.00, 20, "Monitor LG 24 pulgadas Full HD IPS"),
        ("AUDIFONOS001", "Audífonos Sony WH-1000XM4", 1800.00, 15, "Audífonos inalámbricos con cancelación de ruido"),
        ("WEBCAM001", "Webcam Logitech C920", 450.00, 35, "Webcam Full HD 1080p con micrófono"),
        ("USB001", "Memoria USB 64GB", 85.00, 100, "Memoria USB 3.0 de 64GB SanDisk"),
    ]
    
    for sku, nombre, precio, stock, desc in productos_electronica:
        crear_producto(sku, nombre, cat_electronica, precio, stock, desc)
    
    # Crear productos - Oficina
    print("\n📝 Creando productos de Oficina...")
    productos_oficina = [
        ("PLUMA001", "Plumas BIC Cristal x12", 25.00, 200, "Paquete de 12 plumas BIC Cristal azul"),
        ("CUADERNO001", "Cuaderno Profesional 100 hojas", 35.00, 150, "Cuaderno profesional cuadrícula 100 hojas"),
        ("LAPIZ001", "Lápices Mirado x12", 30.00, 180, "Caja de 12 lápices Mirado #2"),
        ("ARCHIVADOR001", "Archivador AZ Carta", 45.00, 100, "Archivador de palanca tamaño carta"),
        ("CLIPS001", "Clips Metalicos x100", 15.00, 250, "Caja de 100 clips metálicos"),
        ("POST001", "Post-it 3x3 x4", 55.00, 120, "Pack de 4 blocks Post-it 3x3 pulgadas"),
        ("ENGRAPADORA001", "Engrapadora Swingline", 85.00, 60, "Engrapadora de escritorio capacidad 20 hojas"),
        ("TIJERAS001", "Tijeras Oficina 8 pulgadas", 35.00, 80, "Tijeras de acero inoxidable 8 pulgadas"),
    ]
    
    for sku, nombre, precio, stock, desc in productos_oficina:
        crear_producto(sku, nombre, cat_oficina, precio, stock, desc)
    
    # Crear productos - Hogar
    print("\n🏠 Creando productos de Hogar...")
    productos_hogar = [
        ("TERMO001", "Termo Stanley 1L", 350.00, 40, "Termo de acero inoxidable Stanley 1 litro"),
        ("TAZA001", "Taza Cerámica 350ml", 45.00, 120, "Taza de cerámica color blanco 350ml"),
        ("LICUADORA001", "Licuadora Oster 3 Velocidades", 650.00, 25, "Licuadora Oster 3 velocidades 600W"),
        ("PLANCHA001", "Plancha de Vapor Black+Decker", 380.00, 30, "Plancha de vapor con suela antiadherente"),
        ("ASPIRADORA001", "Aspiradora Portátil", 420.00, 20, "Aspiradora de mano portátil recargable"),
        ("FOCO001", "Foco LED 12W x4", 95.00, 150, "Pack de 4 focos LED 12W luz blanca"),
    ]
    
    for sku, nombre, precio, stock, desc in productos_hogar:
        crear_producto(sku, nombre, cat_hogar, precio, stock, desc)
    
    # Crear productos - Ropa
    print("\n👕 Creando productos de Ropa...")
    productos_ropa = [
        ("PLAYERA001", "Playera Básica Blanca", 120.00, 100, "Playera 100% algodón color blanco talla M"),
        ("PLAYERA002", "Playera Básica Negra", 120.00, 100, "Playera 100% algodón color negro talla M"),
        ("JEANS001", "Jeans Levis 501", 850.00, 50, "Jeans Levis 501 corte recto"),
        ("SUDADERA001", "Sudadera con Capucha", 380.00, 60, "Sudadera con capucha y bolsa canguro"),
        ("CALCETINES001", "Calcetines x6 Pares", 95.00, 200, "Pack de 6 pares de calcetines"),
    ]
    
    for sku, nombre, precio, stock, desc in productos_ropa:
        crear_producto(sku, nombre, cat_ropa, precio, stock, desc)
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    total_productos = Productos.objects.count()
    total_categorias = Categorias.objects.count()
    
    print(f"\n✅ Total de categorías: {total_categorias}")
    print(f"✅ Total de productos: {total_productos}")
    
    print("\n📦 Productos por categoría:")
    for cat in Categorias.objects.all():
        count = Productos.objects.filter(categoria=cat).count()
        print(f"   - {cat.nombre}: {count} productos")
    
    print("\n🎯 Productos de ejemplo para probar:")
    productos_ejemplo = Productos.objects.all()[:10]
    for p in productos_ejemplo:
        print(f"   - SKU: {p.sku:15} | {p.nombre[:40]:40} | Stock: {p.stock_actual:3} | ${p.precio_venta}")
    
    print("\n" + "="*60)
    print("✅ Base de datos poblada exitosamente!")
    print("\n💡 Ahora puedes probar comandos como:")
    print("   - 'agregar tres unidades del producto LAPTOP001'")
    print("   - 'añadir cinco del MOUSE001'")
    print("   - 'mete dos del TECLADO001'")
    print("   - 'quiero cuatro del USB001'")
    print("="*60 + "\n")


if __name__ == '__main__':
    try:
        poblar_productos()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
