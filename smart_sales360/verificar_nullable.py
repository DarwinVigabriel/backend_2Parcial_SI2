import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_sales360.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT column_name, is_nullable, column_default 
    FROM information_schema.columns 
    WHERE table_name='ventas' AND column_name IN ('subtotal', 'total')
    ORDER BY ordinal_position;
""")

rows = cursor.fetchall()
print("\n🔍 Estructura de columnas subtotal y total en tabla ventas:\n")
for row in rows:
    print(f"  {row[0]}: nullable={row[1]}, default={row[2]}")
