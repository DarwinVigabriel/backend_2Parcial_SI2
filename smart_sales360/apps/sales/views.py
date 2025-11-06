from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction
from django.db.models import Sum, F, Q
import tempfile
import os
import re

# Import opcional de whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ OpenAI Whisper no está instalado. Instala con: pip install openai-whisper")

from .models import Cart, CartItem
from .serializers import (
    CartSerializer, 
    CartItemSerializer, 
    CartItemCreateSerializer,
    VoiceCommandSerializer
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
        Procesar comando de voz para gestionar el carrito usando OpenAI Whisper.
        
        Ejemplos de comandos:
        - "agregar 3 unidades de producto SKU123"
        - "añadir 5 del producto codigo ABC"
        - "eliminar producto SKU456"
        - "quitar item 12"
        - "actualizar cantidad a 10 del item 5"
        - "vaciar carrito"
        - "finalizar compra"
        """
        # Verificar que Whisper está disponible
        if not WHISPER_AVAILABLE:
            return Response(
                {
                    'detail': 'OpenAI Whisper no está instalado',
                    'error': 'Para usar comandos de voz, instala: pip install openai-whisper',
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
        
        # Guardar archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp_file:
            for chunk in audio_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        try:
            # Verificar que Whisper esté disponible
            if not WHISPER_AVAILABLE:
                return Response(
                    {'detail': 'OpenAI Whisper no está instalado. Instala con: pip install openai-whisper'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Cargar modelo Whisper (usar 'base' o 'small' para mejor precisión)
            # Opciones: tiny, base, small, medium, large
            try:
                model = whisper.load_model("small")  # Cambiado de 'base' a 'small' para mejor precisión
            except Exception as model_error:
                # Si falla 'small', intentar con 'base'
                print(f"Error cargando modelo 'small': {model_error}. Intentando con 'base'...")
                try:
                    model = whisper.load_model("base")
                except Exception as base_error:
                    return Response(
                        {'detail': f'Error cargando modelo Whisper: {str(base_error)}'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # Transcribir audio con configuración optimizada
            result = model.transcribe(
                tmp_file_path, 
                language='es',  # Español
                task='transcribe',  # Transcribir (no traducir)
                fp16=False,  # Deshabilitar para compatibilidad
                temperature=0.0,  # Menor temperatura = más determinista
                beam_size=5,  # Búsqueda más exhaustiva
                best_of=5,  # Considerar más opciones
                patience=1.0,  # Más paciencia en la decodificación
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6,
                condition_on_previous_text=True,  # Mejor contexto
                initial_prompt="Comandos de carrito de compras: agregar, eliminar, actualizar, vaciar, finalizar compra, SKU, producto, unidades, cantidad, item."  # Contexto
            )
            transcription = result['text'].strip().lower()
            
            # Procesar comando
            response_data = self._process_voice_command(cart, transcription)
            
            return Response({
                'transcription': transcription,
                'cart_id': str(cart.id),
                **response_data
            })
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error en voice_command: {error_details}")
            return Response(
                {
                    'detail': f'Error procesando audio: {str(e)}',
                    'error_type': type(e).__name__,
                    'error_details': str(e)
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Eliminar archivo temporal
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def _process_voice_command(self, cart, text):
        """Procesar el texto transcrito y ejecutar la acción correspondiente"""
        text = text.lower()
        
        # Normalizar texto (quitar acentos y caracteres especiales)
        import unicodedata
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Comando: Agregar producto
        agregar_palabras = ['agregar', 'anadir', 'aniadir', 'agregame', 'anademe', 'agrégame', 'añádeme', 'agrega', 'añade', 'mete', 'pon', 'poner']
        if any(word in text for word in agregar_palabras):
            return self._voice_add_product(cart, text)
        
        # Comando: Eliminar producto
        eliminar_palabras = ['eliminar', 'quitar', 'borrar', 'sacar', 'elimina', 'quita', 'borra', 'saca', 'remove', 'remover']
        if any(word in text for word in eliminar_palabras):
            return self._voice_remove_item(cart, text)
        
        # Comando: Actualizar cantidad
        actualizar_palabras = ['actualizar', 'cambiar', 'modificar', 'actualiza', 'cambia', 'modifica', 'update']
        if any(word in text for word in actualizar_palabras):
            return self._voice_update_item(cart, text)
        
        # Comando: Vaciar carrito
        vaciar_palabras = ['vaciar', 'limpiar', 'borrar todo', 'eliminar todo', 'vacia', 'limpia', 'clear']
        if any(word in text for word in vaciar_palabras):
            cart.items.all().delete()
            cart.total = 0
            cart.save()
            return {
                'action': 'clear',
                'message': 'Carrito vaciado exitosamente',
                'cart': CartSerializer(cart).data
            }
        
        # Comando: Finalizar compra
        finalizar_palabras = ['finalizar', 'terminar', 'checkout', 'pagar', 'finaliza', 'termina', 'comprar', 'finish']
        if any(word in text for word in finalizar_palabras):
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
        ver_palabras = ['mostrar', 'ver', 'consultar', 'listar', 'muestra', 've', 'show', 'display']
        if any(word in text for word in ver_palabras):
            return {
                'action': 'view',
                'message': 'Contenido del carrito',
                'cart': CartSerializer(cart).data
            }
        
        else:
            return {
                'action': 'unknown',
                'error': 'No se pudo interpretar el comando',
                'transcription': text,
                'suggestion': 'Intenta comandos como: "agregar producto", "eliminar item", "vaciar carrito", "finalizar compra"'
            }

    def _voice_add_product(self, cart, text):
        """Agregar producto por voz"""
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
        
        # Buscar cantidad (priorizar números en dígitos)
        quantity_match = re.search(r'(\d+)\s*(?:unidad|unidades|producto|productos|de)?', text_procesado)
        quantity = int(quantity_match.group(1)) if quantity_match else 1
        
        # Buscar SKU o código de producto (más flexible)
        # Patrones: "SKU ABC123", "codigo ABC123", "producto ABC123"
        sku_patterns = [
            r'(?:sku|codigo|código|producto)\s*([a-zA-Z0-9\-_]+)',
            r'([A-Z]{2,}[0-9]+)',  # Patrón como PROD001, ABC123
            r'([a-zA-Z]+[0-9]{3,})',  # Patrón como prod001, abc123
        ]
        
        sku = None
        for pattern in sku_patterns:
            sku_match = re.search(pattern, text, re.IGNORECASE)
            if sku_match:
                sku = sku_match.group(1).upper()
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
