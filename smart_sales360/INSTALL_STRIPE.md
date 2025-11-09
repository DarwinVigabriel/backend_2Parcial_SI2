# 🚀 Guía Rápida de Instalación - Stripe en CU13

## 1️⃣ Instalar Stripe

### Opción A: Instalación directa
```bash
pip install stripe
```

### Opción B: Desde requirements.txt
```bash
pip install -r requirements.txt
```

---

## 2️⃣ Configurar Variables de Entorno

Edita el archivo `.env` en:
```
backend/smart_sales360/.env
```

Agrega:
```env
# Stripe Configuration
STRIPE_PUBLIC_KEY=pk_test_51234567890abcdefghijklmnopqrstuvwxyz
STRIPE_SECRET_KEY=sk_test_abcdefghijklmnopqrstuvwxyz1234567890
```

**¿Dónde obtener las claves?**
1. Ve a https://stripe.com
2. Inicia sesión en tu cuenta
3. Dashboard → Settings → API Keys (Pestaña "Developers")
4. Copia tu `Publishable key` (pk_test_...) y `Secret key` (sk_test_...)
5. Pega en tu `.env`

---

## 3️⃣ Verificar Instalación

```bash
python -c "import stripe; print(f'Stripe {stripe.__version__} instalado')"
```

**Salida esperada:**
```
Stripe X.XX.X instalado
```

---

## 4️⃣ Probar la Integración

### Iniciar servidor
```bash
python manage.py runserver
```

### Procesar un pago de prueba
```bash
curl -X POST http://127.0.0.1:8000/api/sales/pagos/procesar/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_AUTH_TOKEN" \
  -d '{
    "venta_id": "123e4567-e89b-12d3-a456-426614174000",
    "monto": 10.00,
    "metodo_pago": "tarjeta_credito",
    "tarjeta_numero": "4242424242424242",
    "tarjeta_nombre": "Test User",
    "tarjeta_expiracion": "12/25",
    "tarjeta_cvv": "123"
  }'
```

**Respuesta exitosa (200):**
```json
{
  "id": "550e8400...",
  "estado": "completado",
  "numero_transaccion": "pi_...",
  "tarjeta_ultimos_digitos": "4242"
}
```

---

## 5️⃣ Usar el Script de Ejemplo

```bash
# Edita primero con tus credenciales
nano ejemplo_stripe_cu13.py

# Luego ejecuta
python ejemplo_stripe_cu13.py
```

---

## 📌 Troubleshooting

### ❌ Error: "ImportError: No module named 'stripe'"
```bash
# Solución:
pip install stripe
```

### ❌ Error: "STRIPE_SECRET_KEY no configurada"
- Verifica que `.env` esté en `backend/smart_sales360/.env`
- Verifica que tenga: `STRIPE_SECRET_KEY=sk_test_...`
- Reinicia el servidor

### ❌ Error: "stripe.error.AuthenticationError"
- Verifica que tu `sk_test_` sea válida en https://stripe.com/dashboard
- Copia nuevamente de Dashboard → Settings → API Keys

### ❌ Tarjeta rechazada
- Usa las tarjetas de prueba correctas (ver `STRIPE_INTEGRATION.md`)
- `4242424242424242` = éxito
- `4000000000000002` = rechazo

---

## 📁 Archivos Relacionados

| Archivo | Descripción |
|---------|-------------|
| `STRIPE_INTEGRATION.md` | Documentación completa |
| `STRIPE_RESUMEN.md` | Resumen visual de cambios |
| `ejemplo_stripe_cu13.py` | Script de ejemplo |
| `.env` | Variables de entorno |
| `apps/sales/models.py` | Integración en modelo Pago |
| `apps/sales/serializers.py` | Validación de serializer |

---

## ✅ Verificación Final

- [ ] `stripe` instalado (`pip list | grep stripe`)
- [ ] Variables en `.env` configuradas
- [ ] Servidor inicia sin errores (`python manage.py runserver`)
- [ ] Endpoint accesible (`GET /api/sales/pagos/`)
- [ ] Pago de prueba procesado exitosamente

---

## 🎯 Pasos Siguientes

1. ✅ Instalar Stripe
2. ✅ Configurar `.env`
3. ✅ Procesar primer pago
4. 📖 Leer `STRIPE_INTEGRATION.md` para detalles completos
5. 🧪 Usar `ejemplo_stripe_cu13.py` para pruebas
6. 🚀 Ir a producción (cambiar `sk_test_` a `sk_live_`)

---

**¿Necesitas ayuda?** Consulta:
- `STRIPE_INTEGRATION.md` - Documentación completa
- `STRIPE_RESUMEN.md` - Resumen de cambios
- https://stripe.com/docs - Documentación oficial

---

Última actualización: 2025-11-09
