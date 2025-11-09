# 🚀 INICIO RÁPIDO - CU12 + CU13 con Stripe

## ⚡ En 5 Minutos

### 1️⃣ Instalar Stripe (1 min)
```bash
cd backend/smart_sales360
pip install stripe
```

### 2️⃣ Configurar .env (1 min)
Edita `.env` y agrega:
```env
STRIPE_PUBLIC_KEY=pk_test_51234567890abcdefghijklmnopqrstuvwxyz
STRIPE_SECRET_KEY=sk_test_abcdefghijklmnopqrstuvwxyz1234567890
```

**¿Cómo obtenerlas?**
- Ve a https://stripe.com/dashboard
- Settings → Developers → API Keys
- Copia `Publishable key` y `Secret key`

### 3️⃣ Iniciar Servidor (1 min)
```bash
python manage.py runserver
```

### 4️⃣ Acceder al Admin (1 min)
- Ve a http://127.0.0.1:8000/admin
- Inicia sesión
- Navega a "Ventas" o "Pagos"

### 5️⃣ Crear Venta + Pago (1 min)
- Crea una **Venta** desde el admin
- Agrega **detalles** (productos)
- Crea un **Pago** con tarjeta de prueba

---

## 💳 Tarjetas de Prueba

```
Éxito:    4242 4242 4242 4242
Rechazo:  4000 0000 0000 0002
```

Expiración: 12/25 | CVV: 123

---

## 🔗 Endpoints Principales

### CU12: Crear Venta
```bash
curl -X POST http://127.0.0.1:8000/api/sales/ventas/crear_desde_carrito/ \
  -H "Content-Type: application/json" \
  -d '{"carrito_id": "..."}'
```

### CU13: Procesar Pago
```bash
curl -X POST http://127.0.0.1:8000/api/sales/pagos/procesar/ \
  -H "Content-Type: application/json" \
  -d '{
    "venta_id": "...",
    "monto": 150.00,
    "metodo_pago": "tarjeta_credito",
    "tarjeta_numero": "4242424242424242",
    "tarjeta_nombre": "Test User",
    "tarjeta_expiracion": "12/25",
    "tarjeta_cvv": "123"
  }'
```

---

## 📖 Documentación

| Archivo | Para |
|---------|------|
| `INSTALL_STRIPE.md` | Instalación y configuración |
| `STRIPE_INTEGRATION.md` | Detalles técnicos |
| `STRIPE_RESUMEN.md` | Resumen de cambios |
| `ejemplo_stripe_cu13.py` | Ejemplos de código |

---

## 🎯 Tareas Comunes

### ✅ Crear una venta
1. Admin → Ventas → Agregar venta
2. Seleccionar cliente y vendedor
3. Agregar detalles (productos)
4. Guardar

### ✅ Procesar un pago
1. Admin → Pagos → Agregar pago
2. O usar endpoint: `POST /api/sales/pagos/procesar/`
3. Ingresar datos de tarjeta
4. Stripe procesa automáticamente

### ✅ Ver historial de pagos
1. Admin → Pagos
2. O usar endpoint: `GET /api/sales/pagos/`

---

## ⚠️ Troubleshooting

| Error | Solución |
|-------|----------|
| ImportError: stripe | `pip install stripe` |
| STRIPE_SECRET_KEY missing | Agrega a `.env` |
| Tarjeta rechazada | Usa `4242424242424242` |
| Conexión a Stripe | Verifica conexión a internet |

---

## 🔐 Seguridad

✅ Implementado:
- PCI-DSS Level 1 (Stripe)
- Encriptación HTTPS
- Solo últimos 4 dígitos guardados
- Validación completa

---

## ✨ Características Implementadas

✅ CU12:
- [x] Crear venta desde carrito
- [x] Generar código automático
- [x] Calcular totales automáticamente
- [x] Descuento de stock

✅ CU13:
- [x] Procesar pago con Stripe
- [x] Múltiples métodos (tarjeta, QR, PayPal)
- [x] Generar y validar QR
- [x] Actualizar venta automáticamente

---

## 📊 Flujo Completo

```
Carrito → Venta → Pago Stripe → Venta Pagada ✅
```

---

## 🎯 Checklist

- [ ] Stripe instalado
- [ ] `.env` configurado
- [ ] Servidor ejecutándose
- [ ] Admin accesible
- [ ] Primera venta creada
- [ ] Primer pago procesado

---

## 🚀 ¡Listo!

Todo está configurado. Comienza a usar CU12 y CU13 ahora.

**¿Necesitas ayuda?** Consulta los archivos `.md` en `backend/smart_sales360/`

---

**Última actualización:** 2025-11-09
