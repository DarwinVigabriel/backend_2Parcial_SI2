"""
Script de prueba rápida para CU11: Gestionar Carrito de Compra

Este script verifica que todos los componentes del carrito estén correctamente instalados.
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Verificar que todas las dependencias estén instaladas"""
    print("🔍 Verificando imports...")
    
    try:
        import django
        print("✅ Django instalado:", django.get_version())
    except ImportError as e:
        print("❌ Django no está instalado:", e)
        return False
    
    try:
        import rest_framework
        print("✅ Django REST Framework instalado")
    except ImportError as e:
        print("❌ Django REST Framework no está instalado:", e)
        return False
    
    try:
        import whisper
        print("✅ OpenAI Whisper instalado")
    except ImportError as e:
        print("❌ OpenAI Whisper no está instalado:", e)
        print("   Instala con: pip install openai-whisper")
        return False
    
    try:
        import torch
        print("✅ PyTorch instalado:", torch.__version__)
    except ImportError as e:
        print("❌ PyTorch no está instalado:", e)
        return False
    
    return True


def test_models():
    """Verificar que los modelos estén correctamente definidos"""
    print("\n🔍 Verificando modelos...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_sales360.settings')
        import django
        django.setup()
        
        from apps.sales.models import Cart, CartItem
        print("✅ Modelo Cart importado correctamente")
        print("✅ Modelo CartItem importado correctamente")
        
        # Verificar campos del modelo Cart
        cart_fields = [f.name for f in Cart._meta.get_fields()]
        required_cart_fields = ['id', 'usuario', 'cliente', 'status', 'total', 'items']
        for field in required_cart_fields:
            if field in cart_fields:
                print(f"   ✅ Campo '{field}' existe en Cart")
            else:
                print(f"   ❌ Campo '{field}' NO existe en Cart")
        
        # Verificar campos del modelo CartItem
        item_fields = [f.name for f in CartItem._meta.get_fields()]
        required_item_fields = ['id', 'cart', 'producto', 'quantity', 'price']
        for field in required_item_fields:
            if field in item_fields:
                print(f"   ✅ Campo '{field}' existe en CartItem")
            else:
                print(f"   ❌ Campo '{field}' NO existe en CartItem")
        
        return True
    except Exception as e:
        print("❌ Error al verificar modelos:", e)
        return False


def test_serializers():
    """Verificar que los serializers estén correctamente definidos"""
    print("\n🔍 Verificando serializers...")
    
    try:
        from apps.sales.serializers import (
            CartSerializer, 
            CartItemSerializer, 
            CartItemCreateSerializer,
            VoiceCommandSerializer
        )
        print("✅ CartSerializer importado correctamente")
        print("✅ CartItemSerializer importado correctamente")
        print("✅ CartItemCreateSerializer importado correctamente")
        print("✅ VoiceCommandSerializer importado correctamente")
        return True
    except Exception as e:
        print("❌ Error al verificar serializers:", e)
        return False


def test_views():
    """Verificar que las vistas estén correctamente definidas"""
    print("\n🔍 Verificando vistas...")
    
    try:
        from apps.sales.views import CartViewSet, CartItemViewSet
        print("✅ CartViewSet importado correctamente")
        print("✅ CartItemViewSet importado correctamente")
        
        # Verificar que el método voice_command existe
        if hasattr(CartViewSet, 'voice_command'):
            print("✅ Método voice_command existe en CartViewSet")
        else:
            print("❌ Método voice_command NO existe en CartViewSet")
        
        return True
    except Exception as e:
        print("❌ Error al verificar vistas:", e)
        return False


def test_admin():
    """Verificar que el admin esté configurado"""
    print("\n🔍 Verificando configuración del admin...")
    
    try:
        from apps.sales.admin import CartAdmin, CartItemAdmin
        print("✅ CartAdmin importado correctamente")
        print("✅ CartItemAdmin importado correctamente")
        
        # Verificar que el método test_cart_view existe
        if hasattr(CartAdmin, 'test_cart_view'):
            print("✅ Método test_cart_view existe en CartAdmin")
        else:
            print("❌ Método test_cart_view NO existe en CartAdmin")
        
        return True
    except Exception as e:
        print("❌ Error al verificar admin:", e)
        return False


def test_urls():
    """Verificar que las URLs estén configuradas"""
    print("\n🔍 Verificando configuración de URLs...")
    
    try:
        from apps.sales.urls import router, urlpatterns
        print("✅ URLs de sales importadas correctamente")
        
        # Verificar rutas registradas
        print("   Rutas registradas:")
        for pattern in urlpatterns:
            print(f"   - {pattern.pattern}")
        
        return True
    except Exception as e:
        print("❌ Error al verificar URLs:", e)
        return False


def test_whisper():
    """Verificar que Whisper funciona correctamente"""
    print("\n🔍 Verificando OpenAI Whisper...")
    
    try:
        import whisper
        print("✅ Whisper importado correctamente")
        
        # Intentar cargar el modelo base (más pequeño)
        print("   Intentando cargar modelo 'tiny'...")
        model = whisper.load_model("tiny")
        print("✅ Modelo 'tiny' de Whisper cargado correctamente")
        print("   Nota: En producción se recomienda usar 'base' o 'small'")
        
        return True
    except Exception as e:
        print("❌ Error al verificar Whisper:", e)
        print("   Asegúrate de tener FFmpeg instalado")
        return False


def main():
    """Ejecutar todas las pruebas"""
    print("="*60)
    print("🧪 PRUEBAS DE CU11: GESTIONAR CARRITO DE COMPRA")
    print("="*60)
    
    results = []
    
    # Ejecutar pruebas
    results.append(("Imports", test_imports()))
    results.append(("Modelos", test_models()))
    results.append(("Serializers", test_serializers()))
    results.append(("Vistas", test_views()))
    results.append(("Admin", test_admin()))
    results.append(("URLs", test_urls()))
    results.append(("Whisper", test_whisper()))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{name:20} {status}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("\n📝 Próximos pasos:")
        print("1. Ejecutar migraciones: python manage.py migrate")
        print("2. Crear un superusuario: python manage.py createsuperuser")
        print("3. Iniciar el servidor: python manage.py runserver")
        print("4. Acceder al admin: http://localhost:8000/admin/")
        print("5. Ir a Sales → Carts → 'Probar Carrito (Texto y Voz)'")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
    
    print("="*60)


if __name__ == '__main__':
    main()
