import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_sales360.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Obtener el constraint de metodo_pago
cursor.execute("""
    SELECT 
        con.conname as constraint_name,
        pg_get_constraintdef(con.oid) as constraint_definition
    FROM pg_constraint con
    INNER JOIN pg_class rel ON rel.oid = con.conrelid
    WHERE rel.relname = 'ventas' 
    AND con.conname LIKE '%metodo_pago%';
""")

rows = cursor.fetchall()
print("\n🔍 Constraint de metodo_pago en tabla ventas:\n")
for row in rows:
    print(f"  Nombre: {row[0]}")
    print(f"  Definición: {row[1]}")
    print()

# También obtener el constraint de estado
cursor.execute("""
    SELECT 
        con.conname as constraint_name,
        pg_get_constraintdef(con.oid) as constraint_definition
    FROM pg_constraint con
    INNER JOIN pg_class rel ON rel.oid = con.conrelid
    WHERE rel.relname = 'ventas' 
    AND con.conname LIKE '%estado%';
""")

rows = cursor.fetchall()
print("\n🔍 Constraint de estado en tabla ventas:\n")
for row in rows:
    print(f"  Nombre: {row[0]}")
    print(f"  Definición: {row[1]}")
    print()
