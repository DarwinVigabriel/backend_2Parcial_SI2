# Integración de Stripe en CU13 - Procesar Pago en Línea

## Descripción
CU13 (Procesar Pago en Línea) está integrado con **Stripe** para procesar pagos reales de tarjetas de crédito, QR, PayPal y otros métodos de pago.

## Configuración

### 1. Variables de Entorno (.env)

Agrega las siguientes variables a tu archivo `.env`:

```env
# Stripe Configuration
STRIPE_PUBLIC_KEY=pk_test_... (tu clave pública de prueba)
STRIPE_SECRET_KEY=sk_test_... (tu clave secreta de prueba)
```

### 2. Obtener Credenciales de Stripe

1. Visita https://stripe.com/
2. Crea una cuenta o inicia sesión
3. Ve a tu Dashboard → Settings → API Keys
4. Copia tu `Publishable key` (pk_test_...) y `Secret key` (sk_test_...)
5. Agrega ambas claves a tu `.env`

### 3. Instalar Stripe

```bash
pip install stripe
```

O si usas requirements.txt:

```bash
pip install -r requirements.txt
```

## Métodos de Pago Soportados

### 1. **Tarjeta de Crédito / Débito**
- Método: `tarjeta_credito` o `tarjeta_debito`
- Procesa mediante Stripe PaymentIntent
- Requiere: número, nombre, expiración (MM/YY), CVV

**Tarjetas de prueba en modo Test:**
- Visa: `4242 4242 4242 4242`
- Mastercard: `5555 5555 5555 4444`
- American Express: `3782 822463 10005`
- Decline (rechazada): `4000 0000 0000 0002`

### 2. **Código QR**
- Método: `qr`
- Genera un código QR para pagar
- Se procesa como Alipay/WeChat Pay

### 3. **PayPal**
- Método: `paypal`
- Integración con PayPal a través de Stripe

### 4. **Métodos Alternativos**
- `efectivo`: Se registra pero no se procesa con Stripe
- `transferencia`: Se registra pero no se procesa con Stripe

## Flujo de Procesamiento (CU13)

### Paso 1: Crear Pago

**Endpoint:** `POST /api/sales/pagos/procesar/`

**Request:**
```json
{
  "venta_id": "123e4567-e89b-12d3-a456-426614174000",
  "monto": 150.00,
  "metodo_pago": "tarjeta_credito",
  "tarjeta_numero": "4242424242424242",
  "tarjeta_nombre": "Juan Perez",
  "tarjeta_expiracion": "12/25",
  "tarjeta_cvv": "123",
  "notas": "Pago por compra de productos"
}
```

### Paso 2: Validación

El serializer valida:
- ✅ Número de tarjeta (16 dígitos)
- ✅ Nombre del titular
- ✅ Expiración (MM/YY)
- ✅ CVV (3-4 dígitos)
- ✅ Que la venta exista y no esté pagada

### Paso 3: Procesamiento con Stripe

El modelo `Pago` llama a `procesar_pago()` que:

1. **Inicializa Stripe** con la clave secreta del `.env`
2. **Crea un PaymentIntent** con Stripe
3. **Confirma el pago** con el método de pago específico
4. **Maneja errores** de Stripe (rechazos, etc.)
5. **Actualiza la venta** si el pago es exitoso

```python
# Dentro de procesar_pago():
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

payment_intent = stripe.PaymentIntent.create(
    amount=int(monto * 100),  # Stripe usa centavos
    currency='usd',
    payment_method_types=['card'],
    description=f'Pago para venta {venta.codigo_venta}'
)
```

### Paso 4: Respuesta

**Exitoso (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "venta_id": "123e4567-e89b-12d3-a456-426614174000",
  "monto": "150.00",
  "metodo_pago": "tarjeta_credito",
  "estado": "completado",
  "numero_transaccion": "pi_1234567890abcdefghijklmn",
  "numero_autorizacion": "ch_1234567890abcdefghijklmn",
  "tarjeta_ultimos_digitos": "4242",
  "tarjeta_tipo": "Visa",
  "fecha_procesamiento": "2025-11-09T18:45:00Z"
}
```

**Fallo (400):**
```json
{
  "error": "Tarjeta rechazada: Your card was declined",
  "estado": "fallido",
  "notas": "Pago rechazado por Stripe"
}
```

## Mapeo de Métodos de Pago

Cuando se procesa un pago exitoso, el campo `metodo_pago` de la venta se actualiza:

| Pago Method | Venta Method |
|---|---|
| `tarjeta_credito` | `tarjeta` |
| `tarjeta_debito` | `tarjeta` |
| `qr` | `stripe` |
| `efectivo` | `efectivo` |
| `paypal` | `paypal` |
| `transferencia` | `transferencia` |

## Manejo de Errores

El método `procesar_pago()` captura todos los errores de Stripe:

```python
# Errores capturados:
- stripe.error.CardError          # Tarjeta rechazada
- stripe.error.RateLimitError     # Límite de velocidad
- stripe.error.InvalidRequestError # Solicitud inválida
- stripe.error.AuthenticationError # Error de autenticación
- stripe.error.APIConnectionError  # Error de conexión
- stripe.error.StripeError         # Error general de Stripe
```

Todos los errores se registran en el campo `notas` del pago con estado `fallido`.

## Seguridad

### ⚠️ Importante: NUNCA guardes números de tarjeta completos

El código **SOLO guarda los últimos 4 dígitos**:

```python
# Bien ✅
pago.tarjeta_ultimos_digitos = tarjeta_numero[-4:]  # "4242"

# Nunca hagas esto ❌
pago.tarjeta_numero_completo = tarjeta_numero  # ¡Inseguro!
```

### PCI-DSS Compliance

- Las tarjetas se procesan a través de Stripe (PCI-DSS Level 1)
- No se almacenan números completos en la base de datos
- La comunicación con Stripe es segura (HTTPS/TLS)

## Pruebas

### Test Cards (Modo Test)

```
Visa (éxito):        4242 4242 4242 4242
Mastercard (éxito):  5555 5555 5555 4444
Amex (éxito):        3782 822463 10005
Decline (fallo):     4000 0000 0000 0002
```

**Todos los campos de prueba:**
- Expiración: cualquier fecha futura (ej: 12/25)
- CVV: cualquier número de 3 dígitos (ej: 123)

### Prueba con cURL

```bash
curl -X POST http://127.0.0.1:8000/api/sales/pagos/procesar/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_AUTH_TOKEN" \
  -d '{
    "venta_id": "123e4567-e89b-12d3-a456-426614174000",
    "monto": 150.00,
    "metodo_pago": "tarjeta_credito",
    "tarjeta_numero": "4242424242424242",
    "tarjeta_nombre": "Test User",
    "tarjeta_expiracion": "12/25",
    "tarjeta_cvv": "123"
  }'
```

## API Endpoints para CU13

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/api/sales/pagos/procesar/` | Procesar pago con Stripe |
| GET | `/api/sales/pagos/` | Listar pagos |
| GET | `/api/sales/pagos/{id}/` | Obtener detalle de pago |
| POST | `/api/sales/pagos/{id}/generar_qr/` | Generar QR de pago |
| POST | `/api/sales/pagos/{id}/confirmar_qr/` | Confirmar pago QR |

## Troubleshooting

### Error: "Import 'stripe' could not be resolved"

**Solución:** Instala stripe
```bash
pip install stripe
```

### Error: "STRIPE_SECRET_KEY no configurada"

**Solución:** Agrega a tu `.env`:
```env
STRIPE_SECRET_KEY=sk_test_...
```

### Error: "stripe.error.AuthenticationError"

**Solución:** Verifica que la clave secreta sea válida en https://stripe.com/dashboard

### Error: "Tarjeta rechazada"

**Solución:** Usa una tarjeta de prueba válida. En modo Test, usa:
- `4242 4242 4242 4242` para simular éxito
- `4000 0000 0000 0002` para simular rechazo

## Referencias

- [Stripe API Docs](https://stripe.com/docs/api)
- [PaymentIntent](https://stripe.com/docs/payments/payment-intents)
- [Test Cards](https://stripe.com/docs/testing)
- [Django + Stripe](https://stripe.com/docs/stripe-js/django)

---

**Última actualización:** 2025-11-09
**Versión:** 1.0
