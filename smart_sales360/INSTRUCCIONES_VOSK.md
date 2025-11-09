# 🎤 Migración de Whisper a Vosk

## 📦 Pasos de Instalación

### 1. Instalar dependencias de Python
```powershell
pip install vosk thefuzz python-Levenshtein
```

### 2. Descargar modelo de Vosk en español
```powershell
# Opción 1: Modelo pequeño (50 MB) - Recomendado para desarrollo
# https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip

# Opción 2: Modelo grande (1.4 GB) - Mejor precisión
# https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip
```

### 3. Extraer el modelo
- Descarga: `vosk-model-small-es-0.42.zip`
- Extrae en: `backend/smart_sales360/vosk-model-small-es-0.42/`
- Estructura esperada:
```
backend/smart_sales360/
├── vosk-model-small-es-0.42/
│   ├── am/
│   ├── conf/
│   ├── graph/
│   └── ivector/
├── apps/
├── manage.py
└── ...
```

## 🔧 Cambios Realizados

### 1. Imports actualizados en `views.py`
```python
# ANTES (Whisper):
import whisper
WHISPER_AVAILABLE = True

# DESPUÉS (Vosk + TheFuzz):
from vosk import Model, KaldiRecognizer
from thefuzz import fuzz, process
import wave
import json
VOSK_AVAILABLE = True
FUZZ_AVAILABLE = True
```

### 2. Función `voice_command()` reescrita
- ✅ Usa Vosk en lugar de Whisper
- ✅ Convierte audio a WAV 16kHz mono con FFmpeg
- ✅ Transcribe con KaldiRecognizer
- ✅ Procesa resultado en JSON

### 3. Función `_process_voice_command()` mejorada
- ✅ Usa TheFuzz para matching difuso de comandos
- ✅ Usa Levenshtein distance para mejor coincidencia
- ✅ Más tolerante a errores de transcripción

## 🎯 Ventajas de Vosk sobre Whisper

| Característica | Whisper | Vosk |
|----------------|---------|------|
| Tamaño modelo | 1-3 GB | 50 MB - 1.4 GB |
| Velocidad | Lenta (GPU recomendada) | Rápida (CPU) |
| Offline | ✅ | ✅ |
| Dependencias | PyTorch (grande) | Ligero |
| Latencia | 5-10 segundos | 1-2 segundos |
| Streaming | ❌ | ✅ |

## 📝 Actualizar requirements.txt

```txt
vosk==0.3.45
thefuzz==0.20.0
python-Levenshtein==0.21.1
```

## ✅ Verificación

```powershell
python -c "import vosk; print('Vosk:', vosk.__version__)"
python -c "from thefuzz import fuzz; print('TheFuzz OK')"
python -c "import Levenshtein; print('Levenshtein OK')"
```

## 🚀 Reiniciar servidor

```powershell
python manage.py runserver
```

## 📖 Documentación

- Vosk: https://alphacephei.com/vosk/
- TheFuzz: https://github.com/seatgeek/thefuzz
- Modelos: https://alphacephei.com/vosk/models
