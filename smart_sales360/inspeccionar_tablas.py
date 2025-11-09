"""
Script para inspeccionar la estructura de las tablas existentes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_sales360.settings')
django.setup()

from django.db import connection

def inspect_table(table_name):
    with connection.cursor() as cursor:
        # Obtener columnas de la tabla
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """)
        
        print(f"\n{'='*80}")
        print(f"Tabla: {table_name}")
        print(f"{'='*80}")
        print(f"{'Columna':<30} {'Tipo':<20} {'Nullable':<10} {'Default'}")
        print(f"{'-'*80}")
        
        columns = cursor.fetchall()
        if columns:
            for col in columns:
                print(f"{col[0]:<30} {col[1]:<20} {col[2]:<10} {col[3] or ''}")
        else:
            print(f"❌ La tabla '{table_name}' no existe")
        
        return columns

# Inspeccionar las tres tablas
print("\n🔍 INSPECCIONANDO TABLAS DE LA BASE DE DATOS\n")

ventas_cols = inspect_table('ventas')
venta_detalles_cols = inspect_table('venta_detalles')
pagos_cols = inspect_table('pagos')

print(f"\n{'='*80}")
print("RESUMEN")
print(f"{'='*80}")
print(f"Tabla 'ventas': {len(ventas_cols) if ventas_cols else 0} columnas")
print(f"Tabla 'venta_detalles': {len(venta_detalles_cols) if venta_detalles_cols else 0} columnas")
print(f"Tabla 'pagos': {len(pagos_cols) if pagos_cols else 0} columnas")
print()
