# CU11: Gestionar Carrito de Compra (Web - Texto y Voz)

## 📋 Descripción
Este caso de uso implementa la gestión completa del carrito de compra con soporte para comandos de texto y voz usando OpenAI Whisper.

## 🔧 Características Implementadas

### 1. Modelos de Datos
- **Cart**: Carrito de compra con UUID, usuario, cliente, estado y total
- **CartItem**: Items del carrito con producto, cantidad y precio

### 2. Admin de Django
- Panel administrativo completo para gestionar carritos
- Vista de items inline en el carrito
- Acciones masivas (completar, cancelar)
- Página de prueba interactiva con interfaz gráfica

### 3. API REST (Texto)
Endpoints disponibles en `/api/sales/carts/`:

#### Operaciones CRUD
- `GET /api/sales/carts/` - Listar carritos
- `POST /api/sales/carts/` - Crear carrito
- `GET /api/sales/carts/{id}/` - Obtener carrito
- `PUT /api/sales/carts/{id}/` - Actualizar carrito
- `DELETE /api/sales/carts/{id}/` - Eliminar carrito

#### Acciones Personalizadas
- `POST /api/sales/carts/{id}/add_item/` - Agregar producto
  ```json
  {
    "producto": 1,
    "quantity": 3
  }
  ```

- `POST /api/sales/carts/{id}/remove_item/` - Eliminar item
  ```json
  {
    "item_id": 5
  }
  ```

- `POST /api/sales/carts/{id}/update_item/` - Actualizar cantidad
  ```json
  {
    "item_id": 5,
    "quantity": 10
  }
  ```

- `POST /api/sales/carts/{id}/clear/` - Vaciar carrito

- `POST /api/sales/carts/{id}/checkout/` - Finalizar compra

### 4. API de Voz (OpenAI Whisper)
Endpoint: `POST /api/sales/carts/voice_command/`

**Parámetros:**
- `audio`: Archivo de audio (MP3, WAV, M4A, OGG, FLAC, WEBM)
- `cart_id` (opcional): UUID del carrito

**Comandos de Voz Soportados:**

#### Agregar Productos
- "agregar 3 unidades del producto SKU ABC123"
- "añadir 5 del producto codigo XYZ789"

#### Eliminar Productos
- "eliminar item 5"
- "quitar producto SKU ABC123"

#### Actualizar Cantidad
- "actualizar cantidad a 10 del item 3"
- "cambiar cantidad a 5 del item 2"

#### Otras Acciones
- "vaciar carrito"
- "finalizar compra"
- "mostrar carrito"

**Respuesta:**
```json
{
  "transcription": "agregar 3 unidades del producto sku abc123",
  "cart_id": "uuid-del-carrito",
  "action": "add_item",
  "message": "Se agregaron 3 unidades de Producto X",
  "cart": {
    "id": "uuid",
    "status": "open",
    "total": "150.00",
    "items": [...]
  }
}
```

## 🚀 Cómo Probar

### Método 1: Panel de Administración de Django

1. Inicia el servidor:
   ```bash
   cd backend/smart_sales360
   python manage.py runserver
   ```

2. Accede al admin de Django:
   ```
   http://localhost:8000/admin/
   ```

3. Ve a la sección "Sales" → "Carts"

4. Haz clic en el botón "🎤 Probar Carrito (Texto y Voz)" en la parte superior derecha

5. En la página de prueba podrás:
   - Crear un nuevo carrito
   - Agregar productos por SKU
   - Actualizar cantidades
   - Eliminar items
   - Vaciar el carrito
   - Finalizar la compra
   - **Enviar comandos de voz** grabando audio o subiendo un archivo

### Método 2: API REST Directa

#### Crear un carrito:
```bash
curl -X POST http://localhost:8000/api/sales/carts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "open"}'
```

#### Agregar producto:
```bash
curl -X POST http://localhost:8000/api/sales/carts/{cart_id}/add_item/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"producto": 1, "quantity": 3}'
```

#### Comando de voz:
```bash
curl -X POST http://localhost:8000/api/sales/carts/voice_command/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio=@command.mp3" \
  -F "cart_id=uuid-del-carrito"
```

### Método 3: Postman/Insomnia

1. Importa la colección de endpoints
2. Configura el token de autenticación
3. Prueba cada endpoint según la documentación

## 📝 Requisitos

### Python Packages (ya incluidos en requirements.txt)
```
Django==5.2.7
djangorestframework==3.16.1
openai-whisper==20250625
torch==2.9.0
```

### Crear Productos de Prueba

Antes de probar, crea algunos productos en el admin:

1. Ve a "Products" → "Productos"
2. Crea productos con SKU únicos (Ej: "PROD001", "PROD002")
3. Asegúrate de que tengan stock disponible
4. Define precios de venta

### Migrar la Base de Datos

Si hay cambios en los modelos:
```bash
python manage.py makemigrations
python manage.py migrate
```

## 🎯 Casos de Prueba

### Prueba 1: Agregar Productos por Texto
1. Crear un carrito nuevo
2. Obtener el SKU de un producto existente
3. Agregar 5 unidades usando el endpoint `add_item`
4. Verificar que el total se actualice correctamente

### Prueba 2: Comando de Voz - Agregar
1. Grabar audio diciendo: "agregar 3 unidades del producto SKU PROD001"
2. Enviar al endpoint `voice_command`
3. Verificar transcripción y respuesta
4. Confirmar que el producto se agregó al carrito

### Prueba 3: Comando de Voz - Eliminar
1. Tener items en el carrito
2. Grabar: "eliminar item 5"
3. Verificar que se eliminó correctamente

### Prueba 4: Comando de Voz - Finalizar
1. Grabar: "finalizar compra"
2. Verificar que el carrito cambió a estado "completed"

### Prueba 5: Validaciones
1. Intentar agregar más cantidad que el stock disponible
2. Verificar mensaje de error
3. Intentar finalizar un carrito vacío
4. Verificar validación

## 🐛 Troubleshooting

### Error: "Import whisper could not be resolved"
- Solución: Instalar dependencias
  ```bash
  pip install openai-whisper torch
  ```

### Error: "Cart not found"
- Verificar que el UUID del carrito es correcto
- Verificar que el carrito pertenece al usuario autenticado

### Error: "Stock insuficiente"
- Verificar que el producto tiene stock disponible
- Actualizar el stock del producto en el admin

### Error al procesar audio
- Verificar que el archivo es un formato soportado
- Verificar que el tamaño no supera 25MB
- Verificar que FFmpeg está instalado (requerido por Whisper)

## 📊 Estructura de Archivos

```
backend/smart_sales360/
├── apps/sales/
│   ├── models.py              # Modelos Cart y CartItem
│   ├── serializers.py         # Serializers con VoiceCommandSerializer
│   ├── views.py               # ViewSets con endpoint voice_command
│   ├── admin.py               # Admin personalizado con vista de prueba
│   ├── urls.py                # URLs de la API
│   └── templates/
│       └── admin/sales/
│           ├── cart_test.html        # Interfaz de prueba
│           └── cart/
│               └── change_list.html  # Override del listado
```

## 🔐 Seguridad

- Todos los endpoints requieren autenticación (excepto lectura)
- Los usuarios solo pueden acceder a sus propios carritos
- Validación de stock antes de agregar productos
- Validación de formato y tamaño de archivos de audio
- Sanitización de comandos de voz

## 📈 Mejoras Futuras

1. **Caché**: Implementar Redis para carritos activos
2. **WebSockets**: Actualizaciones en tiempo real del carrito
3. **ML**: Mejorar el procesamiento de lenguaje natural
4. **Idiomas**: Soporte para múltiples idiomas en comandos de voz
5. **Analytics**: Tracking de comandos de voz más usados
6. **Testing**: Agregar tests unitarios y de integración

## 📞 Soporte

Para problemas o preguntas, contactar al equipo de desarrollo.
