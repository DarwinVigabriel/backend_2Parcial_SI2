from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction
from django.db.models import Sum, F, Q
from django.utils import timezone
import tempfile
import os
import re
import json
import wave

# Import de Vosk para reconocimiento de voz
try:
    from vosk import Model, KaldiRecognizer
    import wave
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("⚠️ Vosk no está instalado. Instala con: pip install vosk")

# Import de TheFuzz para matching fuzzy
try:
    from thefuzz import fuzz, process
    FUZZ_AVAILABLE = True
except ImportError:
    FUZZ_AVAILABLE = False
    print("⚠️ TheFuzz no está instalado. Instala con: pip install thefuzz python-Levenshtein")

from .models import Cart, CartItem, Venta, VentaDetalle, Pago
from .serializers import (
    CartSerializer, 
    CartItemSerializer, 
    CartItemCreateSerializer,
    VoiceCommandSerializer,
    VentaSerializer,
    VentaCreateSerializer,
    VentaDetalleSerializer,
    PagoSerializer,
    PagoCreateSerializer,
    PagoQRSerializer
)
from apps.products.models import Productos


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Si es admin/staff, mostrar todos los carritos
        if self.request.user.is_staff or self.request.user.is_superuser:
            return queryset
        # Si es usuario regular, filtrar por sus carritos
        if self.request.user.is_authenticated and hasattr(self.request.user, 'usuarios'):
            return queryset.filter(usuario__user=self.request.user)
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_item(self, request, pk=None):
        """Agregar un producto al carrito"""
        cart = self.get_object()
        
        if cart.status != 'open':
            return Response(
                {'detail': 'No se pueden agregar items a un carrito cerrado'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CartItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            producto = serializer.validated_data['producto']
            quantity = serializer.validated_data['quantity']
            
            # Verificar stock
            if producto.stock_actual < quantity:
                return Response(
                    {'detail': f'Stock insuficiente. Disponible: {producto.stock_actual}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar si el producto ya existe en el carrito
            existing_item = cart.items.filter(producto=producto).first()
            if existing_item:
                existing_item.quantity += quantity
                existing_item.save()
                item = existing_item
            else:
                item = CartItem.objects.create(
                    cart=cart,
                    producto=producto,
                    quantity=quantity,
                    price=producto.precio_venta
                )
            
            # Actualizar total del carrito
            self._update_cart_total(cart)
            
            return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remove_item(self, request, pk=None):
        """Eliminar un producto del carrito"""
        cart = self.get_object()
        item_id = request.data.get('item_id')
        
        if not item_id:
            return Response(
                {'detail': 'Se requiere item_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = cart.items.get(id=item_id)
            item.delete()
            self._update_cart_total(cart)
            return Response(CartSerializer(cart).data)
        except CartItem.DoesNotExist:
            return Response(
                {'detail': 'Item no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def update_item(self, request, pk=None):
        """Actualizar cantidad de un producto en el carrito"""
        cart = self.get_object()
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        
        if not item_id or quantity is None:
            return Response(
                {'detail': 'Se requiere item_id y quantity'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {'detail': 'La cantidad debe ser mayor a 0'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            item = cart.items.get(id=item_id)
            
            # Verificar stock
            if item.producto.stock_actual < quantity:
                return Response(
                    {'detail': f'Stock insuficiente. Disponible: {item.producto.stock_actual}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            item.quantity = quantity
            item.save()
            self._update_cart_total(cart)
            
            return Response(CartSerializer(cart).data)
        except CartItem.DoesNotExist:
            return Response(
                {'detail': 'Item no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'detail': 'Cantidad inválida'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def clear(self, request, pk=None):
        """Vaciar el carrito"""
        cart = self.get_object()
        cart.items.all().delete()
        cart.total = 0
        cart.save()
        return Response(CartSerializer(cart).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def checkout(self, request, pk=None):
        """Finalizar compra"""
        cart = self.get_object()
        
        if cart.status != 'open':
            return Response(
                {'detail': 'El carrito ya fue procesado'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not cart.items.exists():
            return Response(
                {'detail': 'El carrito está vacío'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Marcar como completado
        cart.status = 'completed'
        cart.save()
        
        return Response({
            'detail': 'Compra finalizada exitosamente',
            'cart_id': str(cart.id),
            'total': str(cart.total),
            'items_count': cart.items.count()
        })

    @action(
        detail=False, 
        methods=['post'], 
        permission_classes=[permissions.IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser]
    )
    def voice_command(self, request):
        """
        Procesar comando de voz para gestionar el carrito usando Vosk.
        
        Ejemplos de comandos:
        - "agregar 3 unidades de producto SKU123"
        - "añadir 5 del producto codigo ABC"
        - "eliminar producto SKU456"
        - "quitar item 12"
        - "actualizar cantidad a 10 del item 5"
        - "vaciar carrito"
        - "finalizar compra"
        """
        # Verificar que Vosk está disponible
        if not VOSK_AVAILABLE:
            return Response(
                {
                    'detail': 'Vosk no está instalado',
                    'error': 'Para usar comandos de voz, instala: pip install vosk',
                    'suggestion': 'Usa los endpoints de texto mientras tanto'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        serializer = VoiceCommandSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        audio_file = serializer.validated_data['audio']
        cart_id = serializer.validated_data.get('cart_id')
        
        # Obtener o crear carrito
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id)
            except Cart.DoesNotExist:
                return Response(
                    {'detail': 'Carrito no encontrado'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Buscar carrito abierto del usuario o crear uno nuevo
            if hasattr(request.user, 'usuarios'):
                usuario = request.user.usuarios
                cart = Cart.objects.filter(usuario=usuario, status='open').first()
                if not cart:
                    cart = Cart.objects.create(usuario=usuario, status='open')
            else:
                # Si no hay usuario asociado (admin), crear carrito sin usuario
                cart = Cart.objects.filter(status='open', usuario__isnull=True).first()
                if not cart:
                    cart = Cart.objects.create(status='open')
        
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

    def _process_voice_command(self, cart, text):
        """Procesar el texto transcrito y ejecutar la acción correspondiente"""
        text = text.lower()
        
        # Normalizar texto (quitar acentos y caracteres especiales)
        import unicodedata
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Logging para debugging
        print(f"🎤 Comando recibido: '{text}'")
        
        # Comando: Agregar producto
        agregar_palabras = [
            'agregar', 'anadir', 'aniadir', 'agregame', 'anademe', 
            'agregá', 'añade', 'agrega', 'añadi', 'anade', 'aniade',
            'mete', 'pon', 'poner', 'ponme', 'meter', 'meteme',
            'incluye', 'incluir', 'incluye', 'inclui',
            'quiero', 'dame', 'necesito',
            'comprar', 'compra', 'llevame', 'llevo',
            'add', 'adiciona', 'adicionar'
        ]
        if any(word in text for word in agregar_palabras):
            print(f"✅ Detectado comando: AGREGAR")
            return self._voice_add_product(cart, text)
        
        # Comando: Eliminar producto
        eliminar_palabras = [
            'eliminar', 'quitar', 'borrar', 'sacar', 'elimina', 'quita', 'borra', 'saca',
            'remove', 'remover', 'remueve', 'saque', 'borre', 'quite',
            'descarta', 'descartar', 'cancela', 'cancelar',
            'no quiero', 'no lo quiero', 'ya no', 'fuera',
            'delete', 'drop'
        ]
        if any(word in text for word in eliminar_palabras):
            print(f"✅ Detectado comando: ELIMINAR")
            return self._voice_remove_item(cart, text)
        
        # Comando: Actualizar cantidad
        actualizar_palabras = [
            'actualizar', 'cambiar', 'modificar', 'actualiza', 'cambia', 'modifica',
            'update', 'ajustar', 'ajusta', 'editar', 'edita',
            'poner', 'pon', 'establecer', 'establece',
            'dejar', 'deja', 'pasar', 'pasa'
        ]
        if any(word in text for word in actualizar_palabras):
            # Verificar que también mencione "cantidad" o números para diferenciarlo de agregar
            cantidad_palabras = ['cantidad', 'numero', 'unidades', 'item', 'articulo']
            if any(word in text for word in cantidad_palabras) or re.search(r'a\s+\d+', text):
                print(f"✅ Detectado comando: ACTUALIZAR")
                return self._voice_update_item(cart, text)
        
        # Comando: Vaciar carrito
        vaciar_palabras = [
            'vaciar', 'limpiar', 'borrar todo', 'eliminar todo', 'vacia', 'limpia',
            'clear', 'reset', 'resetear', 'reiniciar',
            'quitar todo', 'sacar todo', 'borrame todo', 'eliminame todo',
            'vacio', 'limpio', 'borra todo', 'quita todo'
        ]
        if any(word in text for word in vaciar_palabras):
            print(f"✅ Detectado comando: VACIAR")
            cart.items.all().delete()
            cart.total = 0
            cart.save()
            return {
                'action': 'clear',
                'message': 'Carrito vaciado exitosamente',
                'cart': CartSerializer(cart).data
            }
        
        # Comando: Finalizar compra
        finalizar_palabras = [
            'finalizar', 'terminar', 'checkout', 'pagar', 'finaliza', 'termina',
            'comprar', 'finish', 'completar', 'completa',
            'hacer pedido', 'hacer compra', 'confirmar',
            'proceder', 'continuar', 'listo',
            'ya esta', 'eso es todo', 'nada mas'
        ]
        if any(word in text for word in finalizar_palabras):
            # Verificar que no sea "agregar" o similar
            if not any(word in text for word in agregar_palabras[:10]):
                print(f"✅ Detectado comando: FINALIZAR")
                if cart.items.exists():
                    cart.status = 'completed'
                    cart.save()
                    return {
                        'action': 'checkout',
                        'message': 'Compra finalizada exitosamente',
                        'total': str(cart.total)
                    }
                else:
                    return {
                        'action': 'checkout',
                        'error': 'El carrito está vacío',
                        'cart': CartSerializer(cart).data
                    }
        
        # Comando: Ver carrito
        ver_palabras = [
            'mostrar', 'ver', 'consultar', 'listar', 'muestra', 've',
            'show', 'display', 'enseña', 'dime', 'que tengo',
            'mi carrito', 'el carrito', 'que hay', 'cuanto',
            'revisar', 'revisa', 'check'
        ]
        if any(word in text for word in ver_palabras):
            print(f"✅ Detectado comando: VER")
            return {
                'action': 'view',
                'message': 'Contenido del carrito',
                'cart': CartSerializer(cart).data
            }
        
        else:
            print(f"❌ Comando no reconocido")
            return {
                'action': 'unknown',
                'error': 'No se pudo interpretar el comando',
                'transcription': text,
                'suggestion': 'Intenta comandos como: "agregar producto", "eliminar item", "vaciar carrito", "finalizar compra"',
                'detected_words': text.split()
            }

    def _voice_add_product(self, cart, text):
        """Agregar producto por voz"""
        print(f"   🔍 Procesando comando AGREGAR")
        print(f"   📝 Texto original: '{text}'")
        
        # Diccionario de números en español a dígitos
        numeros_texto = {
            'cero': '0', 'uno': '1', 'dos': '2', 'tres': '3', 'cuatro': '4',
            'cinco': '5', 'seis': '6', 'siete': '7', 'ocho': '8', 'nueve': '9',
            'diez': '10', 'once': '11', 'doce': '12', 'trece': '13', 'catorce': '14',
            'quince': '15', 'dieciseis': '16', 'diecisiete': '17', 'dieciocho': '18',
            'diecinueve': '19', 'veinte': '20', 'treinta': '30', 'cuarenta': '40',
            'cincuenta': '50', 'sesenta': '60', 'setenta': '70', 'ochenta': '80',
            'noventa': '90', 'cien': '100'
        }
        
        # Reemplazar números en texto por dígitos
        text_procesado = text
        for palabra, numero in numeros_texto.items():
            text_procesado = text_procesado.replace(palabra, numero)
        
        print(f"   📝 Texto procesado: '{text_procesado}'")
        
        # Buscar cantidad (priorizar números en dígitos)
        quantity_match = re.search(r'(\d+)\s*(?:unidad|unidades|producto|productos|de)?', text_procesado)
        quantity = int(quantity_match.group(1)) if quantity_match else 1
        print(f"   🔢 Cantidad detectada: {quantity}")
        
        # Buscar SKU o código de producto (más flexible)
        # Patrones: "SKU ABC123", "codigo ABC123", "producto ABC123", "laptop 001"
        sku_patterns = [
            r'(?:sku|codigo|código|producto)\s*[:=]?\s*([a-zA-Z0-9\-_\s]+?)(?:\s|$)',  # Con palabra clave
            r'\b([A-Z]{2,}[0-9]+)\b',  # Patrón como PROD001, ABC123
            r'\b([a-zA-Z]+\s*[0-9]{3,})\b',  # Patrón como "laptop 001", "prod001"
            r'\b([a-zA-Z]+[0-9]{3,})\b',  # Patrón como "laptop001", "prod001"
        ]
        
        sku = None
        for pattern in sku_patterns:
            sku_match = re.search(pattern, text, re.IGNORECASE)
            if sku_match:
                # Limpiar el SKU (quitar espacios extras, convertir a mayúsculas)
                sku = sku_match.group(1).strip().replace(' ', '').upper()
                print(f"   📋 SKU detectado: '{sku}' (patrón usado: {pattern})")
                break
        
        if sku:
            try:
                # Buscar producto por SKU o código de barras
                producto = Productos.objects.filter(
                    Q(sku__iexact=sku) | Q(codigo_barras__iexact=sku)
                ).first()
                
                if not producto:
                    # Intentar búsqueda parcial
                    producto = Productos.objects.filter(
                        Q(sku__icontains=sku) | Q(nombre__icontains=sku)
                    ).first()
                
                if not producto:
                    return {
                        'action': 'add_item',
                        'error': f'Producto con SKU "{sku}" no encontrado',
                        'suggestion': f'Verifica que el SKU sea correcto. SKU buscado: {sku}',
                        'cart': CartSerializer(cart).data
                    }
                
                if producto.stock_actual < quantity:
                    return {
                        'action': 'add_item',
                        'error': f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock_actual}',
                        'cart': CartSerializer(cart).data
                    }
                
                # Agregar o actualizar item
                existing_item = cart.items.filter(producto=producto).first()
                if existing_item:
                    existing_item.quantity += quantity
                    existing_item.save()
                else:
                    CartItem.objects.create(
                        cart=cart,
                        producto=producto,
                        quantity=quantity,
                        price=producto.precio_venta
                    )
                
                self._update_cart_total(cart)
                
                return {
                    'action': 'add_item',
                    'message': f'Se agregaron {quantity} unidades de {producto.nombre} al carrito',
                    'producto': {
                        'sku': producto.sku,
                        'nombre': producto.nombre,
                        'precio': str(producto.precio_venta),
                        'cantidad': quantity
                    },
                    'cart': CartSerializer(cart).data
                }
            except Exception as e:
                return {
                    'action': 'add_item',
                    'error': f'Error al agregar producto: {str(e)}',
                    'cart': CartSerializer(cart).data
                }
        else:
            return {
                'action': 'add_item',
                'error': 'No se pudo identificar el SKU del producto',
                'transcription': text,
                'suggestion': 'Intenta decir: "agregar 2 unidades del producto SKU ABC123" o "agregar 3 del producto PROD001"',
                'cart': CartSerializer(cart).data
            }

    def _voice_remove_item(self, cart, text):
        """Eliminar item por voz"""
        # Buscar ID del item
        item_match = re.search(r'(?:item|ítem)\s*(\d+)', text)
        
        if item_match:
            item_id = int(item_match.group(1))
            try:
                item = cart.items.get(id=item_id)
                producto_nombre = item.producto.nombre
                item.delete()
                self._update_cart_total(cart)
                return {
                    'action': 'remove_item',
                    'message': f'Se eliminó {producto_nombre} del carrito',
                    'cart': CartSerializer(cart).data
                }
            except CartItem.DoesNotExist:
                return {
                    'action': 'remove_item',
                    'error': f'Item {item_id} no encontrado en el carrito',
                    'cart': CartSerializer(cart).data
                }
        else:
            # Buscar por SKU
            sku_match = re.search(r'(?:sku|codigo|código)\s*([a-zA-Z0-9]+)', text)
            if sku_match:
                sku = sku_match.group(1).upper()
                item = cart.items.filter(producto__sku=sku).first()
                if item:
                    producto_nombre = item.producto.nombre
                    item.delete()
                    self._update_cart_total(cart)
                    return {
                        'action': 'remove_item',
                        'message': f'Se eliminó {producto_nombre} del carrito',
                        'cart': CartSerializer(cart).data
                    }
                else:
                    return {
                        'action': 'remove_item',
                        'error': f'Producto con SKU {sku} no encontrado en el carrito',
                        'cart': CartSerializer(cart).data
                    }
            
            return {
                'action': 'remove_item',
                'error': 'No se pudo identificar el item. Intenta: "eliminar item 5" o "quitar producto SKU ABC123"',
                'cart': CartSerializer(cart).data
            }

    def _voice_update_item(self, cart, text):
        """Actualizar cantidad de item por voz"""
        # Buscar cantidad
        quantity_match = re.search(r'(?:cantidad|a)\s*(\d+)', text)
        if not quantity_match:
            return {
                'action': 'update_item',
                'error': 'No se pudo identificar la nueva cantidad',
                'cart': CartSerializer(cart).data
            }
        
        quantity = int(quantity_match.group(1))
        
        # Buscar ID del item
        item_match = re.search(r'(?:item|ítem)\s*(\d+)', text)
        
        if item_match:
            item_id = int(item_match.group(1))
            try:
                item = cart.items.get(id=item_id)
                
                if item.producto.stock_actual < quantity:
                    return {
                        'action': 'update_item',
                        'error': f'Stock insuficiente para {item.producto.nombre}. Disponible: {item.producto.stock_actual}',
                        'cart': CartSerializer(cart).data
                    }
                
                item.quantity = quantity
                item.save()
                self._update_cart_total(cart)
                
                return {
                    'action': 'update_item',
                    'message': f'Se actualizó la cantidad a {quantity} unidades',
                    'cart': CartSerializer(cart).data
                }
            except CartItem.DoesNotExist:
                return {
                    'action': 'update_item',
                    'error': f'Item {item_id} no encontrado en el carrito',
                    'cart': CartSerializer(cart).data
                }
        else:
            return {
                'action': 'update_item',
                'error': 'No se pudo identificar el item. Intenta: "actualizar cantidad a 5 del item 3"',
                'cart': CartSerializer(cart).data
            }

    def _update_cart_total(self, cart):
        """Actualizar el total del carrito"""
        total = cart.items.aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or 0
        cart.total = total
        cart.save()


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# ============================================================================
# CU12: Registrar Venta - ViewSet
# ============================================================================

class VentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar ventas (CU12)
    
    Endpoints:
    - GET /api/sales/ventas/ - Listar todas las ventas
    - POST /api/sales/ventas/ - Crear una venta desde un carrito
    - GET /api/sales/ventas/{id}/ - Ver detalle de una venta
    - PUT/PATCH /api/sales/ventas/{id}/ - Actualizar venta
    - DELETE /api/sales/ventas/{id}/ - Eliminar venta
    - POST /api/sales/ventas/crear_desde_carrito/ - Crear venta desde carrito
    - POST /api/sales/ventas/{id}/cancelar/ - Cancelar venta
    - GET /api/sales/ventas/ventas_por_cliente/ - Ventas de un cliente específico
    """
    queryset = Venta.objects.all().prefetch_related('detalles', 'detalles__producto')
    serializer_class = VentaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por cliente
        cliente_id = self.request.query_params.get('cliente_id', None)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        # Filtrar por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtrar por tipo de entrega
        tipo_entrega = self.request.query_params.get('tipo_entrega', None)
        if tipo_entrega:
            queryset = queryset.filter(tipo_entrega=tipo_entrega)
        
        # Filtrar por rango de fechas
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        if fecha_desde:
            queryset = queryset.filter(fecha_venta__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_venta__lte=fecha_hasta)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def crear_desde_carrito(self, request):
        """
        Crear una venta desde un carrito existente
        
        Body:
        {
            "cart_id": "uuid-del-carrito",
            "cliente_id": 1,
            "tipo_entrega": "local",
            "descuento": 0,
            "impuesto_porcentaje": 13,
            "direccion_entrega": "Calle 123",
            "notas": "Notas adicionales"
        }
        """
        serializer = VentaCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                venta = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Venta creada exitosamente',
                    'data': VentaSerializer(venta).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancelar una venta y revertir el stock
        
        POST /api/sales/ventas/{id}/cancelar/
        Body: {"motivo": "Razón de la cancelación"}
        """
        venta = self.get_object()
        
        if venta.estado == 'cancelada':
            return Response({
                'success': False,
                'error': 'Esta venta ya está cancelada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if venta.estado == 'pagada':
            return Response({
                'success': False,
                'error': 'No se puede cancelar una venta pagada. Debe solicitar un reembolso.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        motivo = request.data.get('motivo', 'Sin motivo especificado')
        
        try:
            with transaction.atomic():
                # Revertir stock
                for detalle in venta.detalles.all():
                    producto = detalle.producto
                    if producto.stock_actual is not None:
                        producto.stock_actual += detalle.cantidad
                        producto.save()
                
                # Actualizar estado de venta
                venta.estado = 'cancelada'
                venta.notas = f"{venta.notas}\n\nCANCELADA: {motivo}" if venta.notas else f"CANCELADA: {motivo}"
                venta.save()
                
                # Reabrir carrito si existe
                if venta.cart:
                    venta.cart.status = 'open'
                    venta.cart.save()
                
                return Response({
                    'success': True,
                    'message': 'Venta cancelada exitosamente',
                    'data': VentaSerializer(venta).data
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def ventas_por_cliente(self, request):
        """
        Obtener ventas de un cliente específico
        
        GET /api/sales/ventas/ventas_por_cliente/?cliente_id=1
        """
        cliente_id = request.query_params.get('cliente_id')
        
        if not cliente_id:
            return Response({
                'success': False,
                'error': 'Se requiere el parámetro cliente_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ventas = self.get_queryset().filter(cliente_id=cliente_id)
        serializer = VentaSerializer(ventas, many=True)
        
        return Response({
            'success': True,
            'count': ventas.count(),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtener estadísticas de ventas
        
        GET /api/sales/ventas/estadisticas/
        """
        from django.db.models import Count, Sum, Avg
        from datetime import datetime, timedelta
        
        # Últimos 30 días
        fecha_inicio = datetime.now() - timedelta(days=30)
        
        ventas_periodo = self.get_queryset().filter(fecha_venta__gte=fecha_inicio)
        
        stats = {
            'total_ventas': self.get_queryset().count(),
            'ventas_ultimos_30_dias': ventas_periodo.count(),
            'ventas_por_estado': dict(
                self.get_queryset().values('estado').annotate(
                    count=Count('id')
                ).values_list('estado', 'count')
            ),
            'ventas_por_tipo_entrega': dict(
                self.get_queryset().values('tipo_entrega').annotate(
                    count=Count('id')
                ).values_list('tipo_entrega', 'count')
            ),
            'monto_total': self.get_queryset().filter(
                estado='pagada'
            ).aggregate(total=Sum('total'))['total'] or 0,
            'monto_promedio': self.get_queryset().filter(
                estado='pagada'
            ).aggregate(promedio=Avg('total'))['promedio'] or 0,
        }
        
        return Response({
            'success': True,
            'data': stats
        })


# ============================================================================
# CU13: Procesar Pago en Línea - ViewSet
# ============================================================================

class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar pagos (CU13)
    
    Endpoints:
    - GET /api/sales/pagos/ - Listar todos los pagos
    - POST /api/sales/pagos/ - Crear un pago
    - GET /api/sales/pagos/{id}/ - Ver detalle de un pago
    - POST /api/sales/pagos/procesar/ - Procesar un pago (tarjeta/efectivo/etc)
    - POST /api/sales/pagos/generar_qr/ - Generar código QR para pago
    - POST /api/sales/pagos/{id}/confirmar_qr/ - Confirmar pago por QR
    - POST /api/sales/pagos/{id}/reembolsar/ - Reembolsar un pago
    """
    queryset = Pago.objects.all().select_related('venta')
    serializer_class = PagoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por venta
        venta_id = self.request.query_params.get('venta_id', None)
        if venta_id:
            queryset = queryset.filter(venta_id=venta_id)
        
        # Filtrar por método de pago
        metodo_pago = self.request.query_params.get('metodo_pago', None)
        if metodo_pago:
            queryset = queryset.filter(metodo_pago=metodo_pago)
        
        # Filtrar por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def procesar(self, request):
        """
        Procesar un pago (tarjeta, efectivo, transferencia, etc.)
        
        Body:
        {
            "venta_id": "uuid-de-la-venta",
            "monto": 1500.00,
            "metodo_pago": "tarjeta_credito",
            "tarjeta_numero": "4111111111111111",
            "tarjeta_nombre": "Juan Perez",
            "tarjeta_expiracion": "12/25",
            "tarjeta_cvv": "123",
            "notas": "Pago adicional"
        }
        """
        serializer = PagoCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                pago = serializer.save()
                
                response_data = PagoSerializer(pago).data
                
                # Añadir información adicional según el resultado
                if pago.estado == 'completado':
                    response_data['message'] = '¡Pago procesado exitosamente!'
                else:
                    response_data['message'] = 'El pago fue rechazado. Intenta con otro método.'
                
                return Response({
                    'success': pago.estado == 'completado',
                    'data': response_data
                }, status=status.HTTP_201_CREATED if pago.estado == 'completado' else status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def generar_qr(self, request):
        """
        Generar un código QR para pago
        
        Body:
        {
            "venta_id": "uuid-de-la-venta"
        }
        
        Response:
        {
            "success": true,
            "data": {
                "qr_codigo": "QR-V-20240109-0001-123456",
                "qr_imagen_url": "https://...",
                "venta_numero": "V-20240109-0001",
                "monto": "1500.00"
            }
        }
        """
        serializer = PagoQRSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                qr_data = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Código QR generado exitosamente',
                    'data': qr_data
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def confirmar_qr(self, request, pk=None):
        """
        Confirmar un pago realizado por QR
        
        POST /api/sales/pagos/{id}/confirmar_qr/
        Body: {"codigo_confirmacion": "123456"}
        """
        pago = self.get_object()
        
        if pago.metodo_pago != 'qr':
            return Response({
                'success': False,
                'error': 'Este pago no es por código QR'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if pago.estado == 'completado':
            return Response({
                'success': False,
                'error': 'Este pago ya ha sido confirmado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        codigo_confirmacion = request.data.get('codigo_confirmacion')
        
        if not codigo_confirmacion:
            return Response({
                'success': False,
                'error': 'Se requiere el código de confirmación'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Simular validación del código QR
        # En un sistema real, aquí se validaría con el proveedor de QR
        try:
            pago.estado = 'completado'
            pago.numero_autorizacion = f'QR-AUTH-{codigo_confirmacion}'
            pago.fecha_procesamiento = timezone.now()
            pago.save()
            
            # Actualizar estado de la venta
            if pago.venta:
                pago.venta.estado = 'pagada'
                pago.venta.save()
            
            return Response({
                'success': True,
                'message': 'Pago confirmado exitosamente',
                'data': PagoSerializer(pago).data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reembolsar(self, request, pk=None):
        """
        Reembolsar un pago
        
        POST /api/sales/pagos/{id}/reembolsar/
        Body: {"motivo": "Razón del reembolso"}
        """
        pago = self.get_object()
        
        if pago.estado != 'completado':
            return Response({
                'success': False,
                'error': 'Solo se pueden reembolsar pagos completados'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if pago.estado == 'reembolsado':
            return Response({
                'success': False,
                'error': 'Este pago ya ha sido reembolsado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        motivo = request.data.get('motivo', 'Sin motivo especificado')
        
        try:
            with transaction.atomic():
                # Actualizar estado del pago
                pago.estado = 'reembolsado'
                pago.notas = f"{pago.notas}\n\nREEMBOLSADO: {motivo}" if pago.notas else f"REEMBOLSADO: {motivo}"
                pago.save()
                
                # Actualizar estado de la venta
                if pago.venta:
                    pago.venta.estado = 'reembolsada'
                    pago.venta.save()
                    
                    # Revertir stock
                    for detalle in pago.venta.detalles.all():
                        producto = detalle.producto
                        if producto.stock_actual is not None:
                            producto.stock_actual += detalle.cantidad
                            producto.save()
                
                return Response({
                    'success': True,
                    'message': 'Pago reembolsado exitosamente',
                    'data': PagoSerializer(pago).data
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtener estadísticas de pagos
        
        GET /api/sales/pagos/estadisticas/
        """
        from django.db.models import Count, Sum
        
        stats = {
            'total_pagos': self.get_queryset().count(),
            'pagos_por_estado': dict(
                self.get_queryset().values('estado').annotate(
                    count=Count('id')
                ).values_list('estado', 'count')
            ),
            'pagos_por_metodo': dict(
                self.get_queryset().values('metodo_pago').annotate(
                    count=Count('id')
                ).values_list('metodo_pago', 'count')
            ),
            'monto_total_procesado': self.get_queryset().filter(
                estado='completado'
            ).aggregate(total=Sum('monto'))['total'] or 0,
            'monto_total_reembolsado': self.get_queryset().filter(
                estado='reembolsado'
            ).aggregate(total=Sum('monto'))['total'] or 0,
        }
        
        return Response({
            'success': True,
            'data': stats
        })
