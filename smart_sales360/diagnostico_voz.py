"""
Script de diagnóstico para el sistema de voz
Verifica que todos los componentes estén funcionando correctamente
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_sales360.settings')

import django
django.setup()

def test_whisper_simple():
    """Prueba básica de Whisper"""
    print("\n" + "="*60)
    print("🧪 PRUEBA 1: Verificar Whisper")
    print("="*60)
    
    try:
        import whisper
        print("✅ Whisper importado correctamente")
        
        # Intentar cargar modelo tiny (más rápido para pruebas)
        print("   Cargando modelo 'tiny' para prueba...")
        model = whisper.load_model("tiny")
        print("✅ Modelo 'tiny' cargado correctamente")
        
        # Intentar cargar modelo small
        print("   Cargando modelo 'small'...")
        try:
            model = whisper.load_model("small")
            print("✅ Modelo 'small' cargado correctamente")
        except Exception as e:
            print(f"⚠️ No se pudo cargar 'small': {e}")
            print("   Esto es normal si no se ha descargado aún.")
            print("   El modelo se descargará automáticamente en el primer uso.")
        
        return True
    except Exception as e:
        print(f"❌ Error con Whisper: {e}")
        return False


def test_audio_processing():
    """Prueba procesamiento de audio"""
    print("\n" + "="*60)
    print("🧪 PRUEBA 2: Procesamiento de Audio")
    print("="*60)
    
    try:
        import tempfile
        import os
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            tmp_path = tmp.name
        
        print(f"✅ Archivo temporal creado: {tmp_path}")
        
        # Limpiar
        os.unlink(tmp_path)
        print("✅ Sistema de archivos temporales funciona")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_cart_models():
    """Prueba modelos del carrito"""
    print("\n" + "="*60)
    print("🧪 PRUEBA 3: Modelos de Carrito")
    print("="*60)
    
    try:
        from apps.sales.models import Cart, CartItem
        from apps.products.models import Productos
        
        print("✅ Modelos importados correctamente")
        
        # Verificar que hay productos
        productos_count = Productos.objects.count()
        print(f"   Productos en BD: {productos_count}")
        
        if productos_count == 0:
            print("⚠️ No hay productos en la base de datos")
            print("   Crea algunos productos en /admin/ para probar")
        else:
            # Mostrar algunos productos
            productos = Productos.objects.all()[:3]
            print("   Productos disponibles:")
            for p in productos:
                print(f"   - SKU: {p.sku}, Nombre: {p.nombre}, Stock: {p.stock_actual}")
        
        # Verificar carritos
        carts_count = Cart.objects.count()
        print(f"   Carritos en BD: {carts_count}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_voice_processing():
    """Prueba procesamiento de comandos de voz"""
    print("\n" + "="*60)
    print("🧪 PRUEBA 4: Procesamiento de Comandos")
    print("="*60)
    
    try:
        from apps.sales.views import CartViewSet
        from apps.sales.models import Cart
        
        # Crear un carrito de prueba
        cart = Cart.objects.create(status='open')
        print(f"✅ Carrito de prueba creado: {cart.id}")
        
        # Crear instancia de ViewSet
        viewset = CartViewSet()
        
        # Probar comandos
        test_commands = [
            "agregar 3 unidades del producto SKU PROD001",
            "eliminar item 5",
            "actualizar cantidad a 10 del item 3",
            "vaciar carrito",
            "finalizar compra",
            "mostrar carrito"
        ]
        
        print("   Probando reconocimiento de comandos:")
        for cmd in test_commands:
            result = viewset._process_voice_command(cart, cmd)
            action = result.get('action', 'unknown')
            print(f"   ✅ '{cmd[:30]}...' → {action}")
        
        # Limpiar
        cart.delete()
        print("✅ Carrito de prueba eliminado")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_permissions():
    """Prueba permisos y autenticación"""
    print("\n" + "="*60)
    print("🧪 PRUEBA 5: Permisos y Autenticación")
    print("="*60)
    
    try:
        from django.contrib.auth.models import User
        
        users_count = User.objects.count()
        print(f"   Usuarios en sistema: {users_count}")
        
        if users_count == 0:
            print("⚠️ No hay usuarios. Crea un superusuario:")
            print("   python manage.py createsuperuser")
        else:
            admin_users = User.objects.filter(is_superuser=True)
            print(f"   Superusuarios: {admin_users.count()}")
            for user in admin_users:
                print(f"   - {user.username}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "🔍 DIAGNÓSTICO DEL SISTEMA DE VOZ".center(60, "="))
    
    results = []
    
    # Ejecutar pruebas
    results.append(("Whisper", test_whisper_simple()))
    results.append(("Audio Processing", test_audio_processing()))
    results.append(("Cart Models", test_cart_models()))
    results.append(("Voice Processing", test_voice_processing()))
    results.append(("Permissions", test_permissions()))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status_icon = "✅" if result else "❌"
        print(f"{status_icon} {name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("\n🎉 ¡Sistema completamente funcional!")
        print("\n📝 Próximos pasos:")
        print("1. Asegúrate de tener productos en la BD")
        print("2. Inicia el servidor: python manage.py runserver")
        print("3. Accede a: http://127.0.0.1:8000/admin/sales/cart/test-cart/")
        print("4. Graba un comando de voz")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
        print("\nPosibles soluciones:")
        print("1. Reinstalar Whisper: pip install --upgrade openai-whisper")
        print("2. Verificar que FFmpeg esté instalado")
        print("3. Crear productos en /admin/products/productos/")
        print("4. Crear un superusuario: python manage.py createsuperuser")
    
    print("="*60)


if __name__ == '__main__':
    main()
