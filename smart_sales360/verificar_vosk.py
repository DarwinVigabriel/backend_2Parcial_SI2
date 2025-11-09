"""
Script de verificación de migración a Vosk
"""
import sys
import os

print("="*60)
print("🔍 VERIFICACIÓN DE MIGRACIÓN A VOSK")
print("="*60)

# 1. Verificar Vosk
print("\n1. Verificando Vosk...")
try:
    import vosk
    from vosk import Model, KaldiRecognizer
    print(f"   ✅ Vosk instalado correctamente (importación exitosa)")
except ImportError as e:
    print(f"   ❌ Vosk NO instalado: {e}")
    print("   💡 Instala con: pip install vosk")

# 2. Verificar TheFuzz
print("\n2. Verificando TheFuzz...")
try:
    from thefuzz import fuzz, process
    print(f"   ✅ TheFuzz instalado correctamente")
    # Probar funcionalidad
    test_score = fuzz.ratio("agregar", "agrega")
    print(f"   📊 Test fuzzy match 'agregar' vs 'agrega': {test_score}%")
except ImportError as e:
    print(f"   ❌ TheFuzz NO instalado: {e}")
    print("   💡 Instala con: pip install thefuzz")

# 3. Verificar Levenshtein
print("\n3. Verificando python-Levenshtein...")
try:
    import Levenshtein
    print(f"   ✅ Levenshtein instalado correctamente")
except ImportError as e:
    print(f"   ❌ Levenshtein NO instalado: {e}")
    print("   💡 Instala con: pip install python-Levenshtein")

# 4. Verificar wave (built-in)
print("\n4. Verificando wave...")
try:
    import wave
    print(f"   ✅ Wave disponible (built-in)")
except ImportError as e:
    print(f"   ❌ Wave NO disponible: {e}")

# 5. Verificar modelo de Vosk
print("\n5. Verificando modelo de Vosk...")
model_path = os.path.join(os.path.dirname(__file__), 'vosk-model-small-es-0.42')
if os.path.exists(model_path):
    print(f"   ✅ Modelo encontrado en: {model_path}")
    # Verificar estructura
    required_dirs = ['am', 'conf', 'graph', 'ivector']
    for dir_name in required_dirs:
        dir_path = os.path.join(model_path, dir_name)
        if os.path.exists(dir_path):
            print(f"      ✅ {dir_name}/")
        else:
            print(f"      ❌ {dir_name}/ NO ENCONTRADO")
else:
    print(f"   ❌ Modelo NO encontrado en: {model_path}")
    print("   💡 Descarga desde: https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip")

# 6. Verificar FFmpeg
print("\n6. Verificando FFmpeg...")
import subprocess
try:
    result = subprocess.run(['ffmpeg', '-version'], 
                          capture_output=True, 
                          text=True, 
                          timeout=5)
    if result.returncode == 0:
        version_line = result.stdout.split('\n')[0]
        print(f"   ✅ FFmpeg instalado: {version_line[:60]}...")
    else:
        print("   ❌ FFmpeg no funciona correctamente")
except FileNotFoundError:
    print("   ❌ FFmpeg NO está instalado o no está en PATH")
    print("   💡 Instala con: choco install ffmpeg")
except Exception as e:
    print(f"   ❌ Error verificando FFmpeg: {e}")

# 7. Test de Vosk si todo está instalado
print("\n7. Test de carga de modelo Vosk...")
try:
    if os.path.exists(model_path):
        from vosk import Model
        print("   ⏳ Cargando modelo (puede tardar unos segundos)...")
        model = Model(model_path)
        print("   ✅ Modelo cargado exitosamente!")
    else:
        print("   ⏭️ Saltando test (modelo no encontrado)")
except Exception as e:
    print(f"   ❌ Error cargando modelo: {e}")

# Resumen
print("\n" + "="*60)
print("📊 RESUMEN")
print("="*60)

all_ok = True
try:
    import vosk
    from thefuzz import fuzz
    import Levenshtein
    import wave
    if not os.path.exists(model_path):
        all_ok = False
        print("❌ Falta el modelo de Vosk")
except ImportError:
    all_ok = False
    print("❌ Faltan dependencias de Python")

if all_ok:
    print("✅ ¡Todo listo para usar Vosk!")
    print("\n🚀 Próximo paso:")
    print("   python manage.py runserver")
else:
    print("⚠️ Hay componentes faltantes")
    print("\n💡 Instala las dependencias faltantes:")
    print("   pip install vosk thefuzz python-Levenshtein")
    print("   Descarga modelo: https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip")

print("="*60)
