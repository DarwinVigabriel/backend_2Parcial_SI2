"""
NUEVA IMPLEMENTACIÓN DE voice_command CON VOSK
Reemplazar desde la línea "# Guardar archivo temporal" hasta el final del método
"""

        # Guardar archivo temporal original
        original_path = tempfile.mktemp(suffix=os.path.splitext(audio_file.name)[1])
        with open(original_path, 'wb') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)
        
        # Logging detallado del archivo de audio
        file_size = os.path.getsize(original_path)
        print(f"\n{'='*60}")
        print(f"🎤 PROCESANDO AUDIO CON VOSK")
        print(f"{'='*60}")
        print(f"📁 Nombre original: {audio_file.name}")
        print(f"📦 Tamaño: {file_size} bytes ({file_size/1024:.2f} KB)")
        print(f"🗂️ Tipo MIME: {audio_file.content_type}")
        
        # Verificar que el archivo no esté vacío
        if file_size < 100:
            print(f"⚠️ ADVERTENCIA: Archivo muy pequeño ({file_size} bytes)")
            os.unlink(original_path)
            return Response({
                'detail': f'El archivo de audio es demasiado pequeño ({file_size} bytes). Por favor, graba al menos 1-2 segundos.',
                'transcription': '',
                'suggestion': 'Asegúrate de hablar durante la grabación y que el indicador de nivel muestre >5%.',
                'cart_id': str(cart.id),
                'debug_info': {
                    'file_size': file_size,
                    'file_name': audio_file.name,
                    'content_type': audio_file.content_type
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Archivo WAV temporal para Vosk
        wav_path = tempfile.mktemp(suffix='.wav')
        
        try:
            # Convertir a WAV 16kHz mono (requerido por Vosk)
            import subprocess
            print(f"⏳ Convirtiendo audio a formato WAV 16kHz mono...")
            conversion_result = subprocess.run(
                ['ffmpeg', '-y', '-i', original_path, '-ar', '16000', '-ac', '1', '-f', 'wav', wav_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if conversion_result.returncode != 0:
                raise Exception(f"Error en conversión FFmpeg: {conversion_result.stderr[:200]}")
            
            print(f"✅ Audio convertido a WAV 16kHz mono")
            
            # Cargar modelo de Vosk (español)
            model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'vosk-model-small-es-0.42')
            model_path = os.path.abspath(model_path)
            
            if not os.path.exists(model_path):
                return Response({
                    'detail': 'Modelo de Vosk no encontrado',
                    'error': f'Descarga el modelo desde: https://alphacephei.com/vosk/models',
                    'suggestion': f'Descarga vosk-model-small-es-0.42.zip y extráelo en: {model_path}',
                    'help_url': 'https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            print(f"⏳ Cargando modelo de Vosk desde: {model_path}")
            model = Model(model_path)
            print(f"✅ Modelo de Vosk cargado correctamente")
            
            # Transcribir audio con Vosk
            print(f"⏳ Transcribiendo audio...")
            wf = wave.open(wav_path, "rb")
            
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                wf.close()
                raise Exception("Audio debe ser WAV 16kHz mono PCM")
            
            rec = KaldiRecognizer(model, wf.getframerate())
            rec.SetWords(True)
            rec.SetMaxAlternatives(0)
            
            transcription_parts = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if 'text' in result and result['text']:
                        transcription_parts.append(result['text'])
            
            # Obtener resultado final
            final_result = json.loads(rec.FinalResult())
            if 'text' in final_result and final_result['text']:
                transcription_parts.append(final_result['text'])
            
            wf.close()
            
            transcription = ' '.join(transcription_parts).strip().lower()
            
            print(f"✅ Transcripción completada")
            print(f"📝 Texto transcrito: '{transcription}'")
            print(f"   - Longitud: {len(transcription)} caracteres")
            print(f"   - Vacío: {not transcription}")
            
            # Verificar solo que no esté vacío
            if not transcription:
                print(f"⚠️ AUDIO RECHAZADO: Transcripción vacía")
                return Response({
                    'detail': 'No se detectó audio válido. Por favor, habla más fuerte y cerca del micrófono.',
                    'transcription': transcription,
                    'suggestion': 'Asegúrate de que el micrófono esté funcionando y habla claramente.',
                    'cart_id': str(cart.id),
                    'debug_info': {
                        'file_size': file_size,
                        'transcription_length': len(transcription)
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Logging
            print(f"✅ AUDIO ACEPTADO: Transcripción válida")
            print(f"🎤 Transcripción exitosa: '{transcription}'")
            print(f"{'='*60}\n")
            
            # Procesar comando con TheFuzz para mejor matching
            response_data = self._process_voice_command(cart, transcription)
            
            return Response({
                'transcription': transcription,
                'cart_id': str(cart.id),
                **response_data
            })
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Error en voice_command: {error_details}")
            return Response(
                {
                    'detail': f'Error procesando audio: {str(e)}',
                    'error_type': type(e).__name__,
                    'error_details': str(e)
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Eliminar archivos temporales
            if os.path.exists(original_path):
                try:
                    os.unlink(original_path)
                except:
                    pass
            if os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except:
                    pass
