"""
Script de diagnóstico completo para problemas de audio en CU11
"""
import os
import sys
import subprocess
import tempfile

def check_ffmpeg():
    """Verificar FFmpeg"""
    print("=" * 60)
    print("1. VERIFICANDO FFMPEG")
    print("=" * 60)
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg instalado: {version_line}")
            return True
        else:
            print("❌ FFmpeg no funciona correctamente")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg NO está instalado o no está en PATH")
        print("\n📥 SOLUCIÓN:")
        print("   1. Descarga FFmpeg desde: https://www.gyan.dev/ffmpeg/builds/")
        print("   2. Extrae el archivo")
        print("   3. Agrega la carpeta 'bin' al PATH de Windows")
        print("   4. Reinicia VS Code/Terminal")
        return False
    except Exception as e:
        print(f"❌ Error verificando FFmpeg: {e}")
        return False

def check_whisper():
    """Verificar OpenAI Whisper"""
    print("\n" + "=" * 60)
    print("2. VERIFICANDO OPENAI WHISPER")
    print("=" * 60)
    try:
        import whisper
        print("✅ OpenAI Whisper está instalado")
        
        # Verificar modelos disponibles
        models_available = ['tiny', 'base', 'small', 'medium', 'large']
        print("\n📦 Modelos disponibles:")
        for model_name in models_available:
            print(f"   - {model_name}")
        
        return True
    except ImportError:
        print("❌ OpenAI Whisper NO está instalado")
        print("\n📥 SOLUCIÓN:")
        print("   pip install openai-whisper")
        return False

def check_torch():
    """Verificar PyTorch"""
    print("\n" + "=" * 60)
    print("3. VERIFICANDO PYTORCH")
    print("=" * 60)
    try:
        import torch
        print(f"✅ PyTorch instalado: versión {torch.__version__}")
        print(f"   CUDA disponible: {torch.cuda.is_available()}")
        return True
    except ImportError:
        print("❌ PyTorch NO está instalado")
        print("\n📥 SOLUCIÓN:")
        print("   pip install torch torchaudio")
        return False

def test_whisper_with_silence():
    """Probar Whisper con silencio"""
    print("\n" + "=" * 60)
    print("4. PROBANDO WHISPER CON AUDIO SILENCIOSO")
    print("=" * 60)
    
    if not check_whisper():
        return False
    
    try:
        import whisper
        import numpy as np
        from scipy.io import wavfile
        
        # Crear audio silencioso de 2 segundos
        sample_rate = 16000
        duration = 2
        silence = np.zeros(sample_rate * duration, dtype=np.int16)
        
        # Guardar en archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wavfile.write(tmp.name, sample_rate, silence)
            tmp_path = tmp.name
        
        try:
            print("⏳ Cargando modelo 'tiny' (más rápido)...")
            model = whisper.load_model("tiny")
            print("✅ Modelo cargado correctamente")
            
            print("⏳ Transcribiendo silencio...")
            result = model.transcribe(tmp_path, language='es')
            transcription = result['text'].strip()
            
            print(f"📝 Resultado: '{transcription}'")
            if not transcription:
                print("✅ Whisper detecta correctamente audio silencioso (texto vacío)")
            else:
                print("⚠️ Whisper detectó algo en el silencio (puede ser alucinación)")
            
            return True
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        print(f"❌ Error probando Whisper: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_browser_audio_format():
    """Información sobre formatos de audio del navegador"""
    print("\n" + "=" * 60)
    print("5. FORMATOS DE AUDIO DEL NAVEGADOR")
    print("=" * 60)
    print("📱 MediaRecorder en navegadores genera:")
    print("   - Chrome/Edge: audio/webm (codec opus)")
    print("   - Firefox: audio/webm (codec opus)")
    print("   - Safari: audio/mp4 (codec aac)")
    print("\n✅ WebM con Opus es un formato válido")
    print("⚠️ Requiere FFmpeg para procesarlo con Whisper")

def get_recommendations():
    """Obtener recomendaciones"""
    print("\n" + "=" * 60)
    print("6. RECOMENDACIONES")
    print("=" * 60)
    
    print("\n🔧 Si el audio sigue sin funcionar:")
    print("\n   A) Verifica la duración de la grabación:")
    print("      - Graba al menos 2-3 segundos")
    print("      - Habla claramente durante la grabación")
    print("      - No hagas pausas muy largas")
    
    print("\n   B) Verifica el nivel de audio:")
    print("      - El indicador debe mostrar >5%")
    print("      - Si es 0%, el micrófono no está capturando")
    print("      - Ajusta el volumen del micrófono en Windows")
    
    print("\n   C) Prueba con archivo de audio:")
    print("      - Graba un mensaje de voz en tu teléfono")
    print("      - Transfiérelo a la PC")
    print("      - Súbelo usando 'Subir Archivo de Audio'")
    
    print("\n   D) Verifica permisos del navegador:")
    print("      - Abre Configuración del sitio")
    print("      - Verifica que 'Micrófono' esté 'Permitido'")
    print("      - Intenta en modo incógnito")
    
    print("\n   E) Logs del servidor:")
    print("      - Revisa la consola donde corre Django")
    print("      - Busca mensajes de error de Whisper")
    print("      - Busca el mensaje '🎤 Transcripción exitosa'")

def main():
    print("🔍 DIAGNÓSTICO COMPLETO DE AUDIO - CU11")
    print("=" * 60)
    
    ffmpeg_ok = check_ffmpeg()
    whisper_ok = check_whisper()
    torch_ok = check_torch()
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"FFmpeg:  {'✅' if ffmpeg_ok else '❌'}")
    print(f"Whisper: {'✅' if whisper_ok else '❌'}")
    print(f"PyTorch: {'✅' if torch_ok else '❌'}")
    
    if ffmpeg_ok and whisper_ok and torch_ok:
        print("\n✅ Todos los componentes están instalados")
        test_whisper_with_silence()
    else:
        print("\n❌ Faltan componentes. Instálalos antes de continuar.")
    
    check_browser_audio_format()
    get_recommendations()
    
    print("\n" + "=" * 60)
    print("SIGUIENTE PASO")
    print("=" * 60)
    print("1. Si FFmpeg no está instalado, instálalo primero")
    print("2. Reinicia el servidor Django: python manage.py runserver")
    print("3. Prueba grabando con el indicador de nivel en verde (>5%)")
    print("4. Si sigue sin funcionar, prueba subiendo un archivo de audio")

if __name__ == '__main__':
    main()
