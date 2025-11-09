# 📋 CU12 y CU13 - Implementación Completa

## 🎯 Casos de Uso Implementados

### CU12: Registrar Venta
Sistema completo para crear ventas desde carritos de compra, con cálculo automático de totales, descuentos, impuestos y actualización de inventario.

### CU13: Procesar Pago en Línea
Sistema de procesamiento de pagos con múltiples métodos (tarjeta, efectivo, QR, transferencia) con simulación de validación y generación de códigos QR.

---

## 📁 Archivos Modificados/Creados

### Modelos (`apps/sales/models.py`)
✅ **Venta**: Modelo principal de ventas
- Campos: numero_venta (auto-generado), cliente, usuario, subtotal, descuento, impuesto, total, estado, tipo_venta
- Métodos: Auto-generación de número de venta (V-YYYYMMDD-XXXX)

✅ **VentaDetalle**: Detalles de productos en cada venta
- Campos: venta, producto, cantidad, precio_unitario, descuento_item, subtotal
- Guarda snapshot del producto (nombre, SKU) para historial

✅ **Pago**: Registro de pagos
- Campos: venta, monto, metodo_pago, estado, tarjeta (enmascarada), qr_codigo
- Métodos: procesar_pago() simula validación (90% éxito)

### Serializers (`apps/sales/serializers.py`)
✅ **VentaSerializer**: CRUD completo de ventas
✅ **VentaCreateSerializer**: Crear venta desde carrito
✅ **PagoSerializer**: CRUD completo de pagos
✅ **PagoCreateSerializer**: Procesar pagos con validación de tarjeta
✅ **PagoQRSerializer**: Generar códigos QR

### Views (`apps/sales/views.py`)
✅ **VentaViewSet**: 
- Endpoints CRUD + acciones personalizadas
- `/api/sales/ventas/crear_desde_carrito/` - Crear venta desde carrito
- `/api/sales/ventas/{id}/cancelar/` - Cancelar venta y revertir stock
- `/api/sales/ventas/estadisticas/` - Estadísticas de ventas

✅ **PagoViewSet**:
- Endpoints CRUD + acciones personalizadas
- `/api/sales/pagos/procesar/` - Procesar pago (tarjeta/efectivo/etc)
- `/api/sales/pagos/generar_qr/` - Generar código QR
- `/api/sales/pagos/{id}/confirmar_qr/` - Confirmar pago por QR
- `/api/sales/pagos/{id}/reembolsar/` - Reembolsar pago

### Admin (`apps/sales/admin.py`)
✅ **VentaAdmin**: Panel de administración completo
- Lista con badges de estado y tipo
- Inlines para detalles y pagos
- Acciones: cancelar ventas, exportar a CSV
- Vista personalizada: crear venta desde carrito

✅ **PagoAdmin**: Panel de administración de pagos
- Lista con badges de método y estado
- Vista previa de códigos QR
- Acciones: procesar pagos, reembolsar
- Vistas personalizadas: procesar pago, generar QR

### Templates HTML
✅ **crear_venta_desde_carrito.html**
- Formulario interactivo para crear ventas
- Vista previa del carrito
- Cálculo automático de totales con descuentos e impuestos
- Validación en frontend

✅ **procesar_pago.html**
- Formulario de pago con múltiples métodos
- Simulación de tarjeta de crédito (visual)
- Vista previa de la venta
- Validación de campos de tarjeta

✅ **generar_qr.html**
- Interfaz para generar códigos QR
- Explicación del flujo de pago por QR
- Features del método de pago
- Instrucciones paso a paso

### URLs (`apps/sales/urls.py`)
✅ Registrados nuevos routers:
- `/api/sales/ventas/` - CRUD de ventas
- `/api/sales/pagos/` - CRUD de pagos

### Migraciones
✅ **0002_venta_pago_ventadetalle.py**
- Crea tablas: ventas, venta_detalles, pagos
- Relaciones FK con clientes, usuarios, productos, carritos

---

## 🚀 Cómo Usar

### 1. Iniciar el Servidor
```powershell
python manage.py runserver
```

### 2. Acceder al Panel de Administración
```
http://localhost:8000/admin/
```

### 3. CU12: Crear una Venta

#### Opción A: Desde el Panel de Ventas
1. Ve a **Ventas** en el menú lateral
2. Haz clic en **"Crear Venta desde Carrito"** (botón superior)
3. Selecciona un carrito abierto
4. Selecciona el cliente
5. Configura descuento e impuesto (IVA 13% por defecto)
6. Añade notas opcionales
7. Haz clic en **"✅ Crear Venta"**

**Resultado:**
- ✅ Se crea la venta con número auto-generado
- ✅ Se copian todos los items del carrito a detalles de venta
- ✅ Se actualiza el stock de cada producto
- ✅ Se cierra el carrito (status = 'completed')
- ✅ Estado de venta = 'pendiente'

#### Opción B: Desde la API
```bash
POST /api/sales/ventas/crear_desde_carrito/
Content-Type: application/json

{
  "cart_id": "uuid-del-carrito",
  "cliente_id": 1,
  "tipo_venta": "mostrador",
  "descuento": 10.00,
  "impuesto_porcentaje": 13,
  "notas": "Cliente frecuente"
}
```

### 4. CU13: Procesar un Pago

#### Método 1: Pago con Tarjeta
1. Ve a **Pagos** en el menú lateral
2. Haz clic en **"Procesar Pago"** (botón superior)
3. Selecciona la venta a pagar
4. Elige método: **Tarjeta de Crédito** o **Tarjeta de Débito**
5. Completa los datos de la tarjeta (simulados):
   - Número: 4111111111111111 (16 dígitos)
   - Nombre: JUAN PEREZ
   - Expiración: 12/25
   - CVV: 123
6. Haz clic en **"✅ Procesar Pago"**

**Resultado:**
- ✅ Se crea el pago con número de transacción único
- ✅ Se simula procesamiento (90% de éxito)
- ✅ Se guarda solo los últimos 4 dígitos de la tarjeta
- ✅ Se genera número de autorización
- ✅ Estado de venta cambia a 'pagada'

#### Método 2: Pago con QR
1. Ve a **Pagos** en el menú lateral
2. Haz clic en **"Generar Código QR"** (botón superior)
3. Selecciona la venta
4. Haz clic en **"📱 Generar Código QR"**
5. El sistema genera:
   - Código QR único
   - URL de imagen QR
   - Pago en estado 'pendiente'

**Para confirmar el pago por QR:**
1. Ve al pago creado
2. En el panel de administración, usa la acción **"Confirmar QR"**
3. Ingresa código de confirmación
4. El pago se marca como 'completado'

#### Método 3: Efectivo/Transferencia
1. Similar al método de tarjeta
2. Solo requiere monto y método de pago
3. No requiere datos adicionales

### 5. Gestión de Ventas

#### Cancelar una Venta
1. Ve a la lista de **Ventas**
2. Selecciona las ventas a cancelar
3. En acciones, elige **"Cancelar ventas seleccionadas"**
4. Confirma

**Resultado:**
- ✅ Estado cambia a 'cancelada'
- ✅ Se revierte el stock de todos los productos
- ✅ Se reabre el carrito (si existe)

#### Ver Estadísticas
```bash
GET /api/sales/ventas/estadisticas/
```

Retorna:
- Total de ventas
- Ventas últimos 30 días
- Ventas por estado
- Ventas por tipo
- Monto total recaudado
- Monto promedio por venta

### 6. Gestión de Pagos

#### Reembolsar un Pago
1. Ve al pago completado
2. En el panel, usa la acción **"Reembolsar"**
3. Ingresa motivo del reembolso
4. Confirma

**Resultado:**
- ✅ Estado del pago cambia a 'reembolsado'
- ✅ Estado de la venta cambia a 'reembolsada'
- ✅ Se revierte el stock de todos los productos

---

## 📊 Flujo Completo de una Venta

```
1. CREAR CARRITO
   └─> POST /api/sales/carts/
       { "cliente": 1, "usuario": 1 }

2. AGREGAR PRODUCTOS AL CARRITO
   └─> POST /api/sales/carts/{id}/add_item/
       { "producto": "001", "quantity": 2 }

3. CREAR VENTA DESDE CARRITO (CU12)
   └─> POST /api/sales/ventas/crear_desde_carrito/
       { "cart_id": "uuid", "cliente_id": 1, "impuesto_porcentaje": 13 }
       
   Resultado: Venta creada con estado 'pendiente'

4. PROCESAR PAGO (CU13)
   └─> POST /api/sales/pagos/procesar/
       { 
         "venta_id": "uuid",
         "monto": 1500.00,
         "metodo_pago": "tarjeta_credito",
         "tarjeta_numero": "4111111111111111",
         "tarjeta_nombre": "JUAN PEREZ",
         "tarjeta_expiracion": "12/25",
         "tarjeta_cvv": "123"
       }
       
   Resultado: Pago procesado, venta marcada como 'pagada'

5. CONFIRMAR VENTA
   └─> Venta completada exitosamente
       - Stock actualizado
       - Cliente notificado
       - Registro de auditoría creado
```

---

## 🎨 Características Destacadas

### Seguridad
- 🔒 Enmascaramiento de tarjetas (solo últimos 4 dígitos)
- 🔐 Validación de campos en frontend y backend
- ✅ Transacciones atómicas en base de datos
- 📝 Registro de auditoría completo

### Usabilidad
- 🎨 Interfaces modernas con gradientes y badges
- 📱 Diseño responsive
- ⚡ Validación en tiempo real
- 🔔 Mensajes de confirmación claros

### Funcionalidades
- 📊 Estadísticas en tiempo real
- 📄 Exportación a CSV
- 🔄 Revertir stock en cancelaciones
- 💰 Cálculo automático de totales
- 📱 Generación de códigos QR
- 🎯 Múltiples métodos de pago

### Simulación Realista
- 💳 Vista previa de tarjetas
- 📱 Códigos QR funcionales
- ⏱️ Tiempo de procesamiento simulado
- ✅ Tasa de éxito 90% en pagos

---

## 🧪 Datos de Prueba

### Tarjetas de Prueba (Simuladas)
```
Visa:
  Número: 4111111111111111
  Nombre: JUAN PEREZ
  Exp: 12/25
  CVV: 123

Mastercard:
  Número: 5555555555554444
  Nombre: MARIA LOPEZ
  Exp: 06/26
  CVV: 456

American Express:
  Número: 378282246310005
  Nombre: CARLOS RUIZ
  Exp: 09/27
  CVV: 1234
```

### Escenarios de Prueba
1. **Venta Exitosa**: Carrito → Venta → Pago Exitoso
2. **Pago Fallido**: Pago rechazado (10% probabilidad)
3. **Cancelación**: Crear venta → Cancelar → Verificar stock
4. **Reembolso**: Pago exitoso → Reembolsar → Verificar stock
5. **QR**: Generar QR → Confirmar pago manual

---

## 📌 Notas Importantes

1. **Stock**: Se actualiza automáticamente en ventas y se revierte en cancelaciones/reembolsos
2. **Números de Venta**: Formato V-YYYYMMDD-XXXX (auto-generado)
3. **Números de Transacción**: Formato PAY-YYYYMMDDHHMMSS-XXXX (auto-generado)
4. **Impuesto por Defecto**: 13% (configurable por venta)
5. **Estado de Carritos**: 'open' → 'completed' al crear venta
6. **Estado de Ventas**: 'pendiente' → 'pagada' al confirmar pago

---

## 🐛 Troubleshooting

### Error: "El carrito está vacío"
- Verifica que el carrito tenga items antes de crear la venta

### Error: "Esta venta ya ha sido pagada"
- No se puede procesar un pago para una venta ya pagada
- Usa reembolso si necesitas revertir

### Error: "Cliente no encontrado"
- Verifica que el cliente exista y esté activo
- Crea el cliente primero si es necesario

### Stock negativo
- El sistema permite stock negativo para evitar bloqueos
- Configura alertas de stock mínimo en productos

---

## ✅ Estado Final

✅ **Modelos**: Creados y migrados
✅ **Serializers**: Implementados con validaciones
✅ **Views**: ViewSets completos con acciones
✅ **URLs**: Endpoints registrados
✅ **Admin**: Paneles personalizados
✅ **Templates**: 3 interfaces HTML creadas
✅ **Migraciones**: Aplicadas a la base de datos

**¡Todo listo para usar en el panel de administración!**

🚀 Ejecuta `python manage.py runserver` y accede a http://localhost:8000/admin/
