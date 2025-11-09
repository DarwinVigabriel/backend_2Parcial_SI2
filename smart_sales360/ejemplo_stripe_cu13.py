"""
Script de ejemplo para procesar pagos con Stripe en CU13
Demuestra cómo hacer un POST a la API de pagos
"""

import requests
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
BASE_URL = "http://127.0.0.1:8000/api"
AUTH_TOKEN = "your_auth_token_here"  # Reemplaza con tu token real

# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Token {AUTH_TOKEN}"
}

def procesar_pago_tarjeta(venta_id, monto, tarjeta_numero, tarjeta_nombre, 
                          tarjeta_expiracion, tarjeta_cvv, notas=""):
    """
    Procesa un pago con tarjeta de crédito/débito
    
    Ejemplo de tarjetas de prueba:
    - Visa: 4242 4242 4242 4242
    - Mastercard: 5555 5555 5555 4444
    - American Express: 3782 822463 10005
    - Decline: 4000 0000 0000 0002
    """
    
    payload = {
        "venta_id": venta_id,
        "monto": float(monto),
        "metodo_pago": "tarjeta_credito",
        "tarjeta_numero": tarjeta_numero,
        "tarjeta_nombre": tarjeta_nombre,
        "tarjeta_expiracion": tarjeta_expiracion,  # Formato: MM/YY
        "tarjeta_cvv": tarjeta_cvv,
        "notas": notas
    }
    
    print("\n📋 Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/sales/pagos/procesar/",
            headers=headers,
            json=payload
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        print("📊 Response:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json()
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


def procesar_pago_qr(venta_id, monto, notas=""):
    """
    Procesa un pago con código QR
    """
    
    payload = {
        "venta_id": venta_id,
        "monto": float(monto),
        "metodo_pago": "qr",
        "notas": notas
    }
    
    print("\n📋 Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/sales/pagos/procesar/",
            headers=headers,
            json=payload
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        print("📊 Response:")
        result = response.json()
        print(json.dumps(result, indent=2))
        
        # Mostrar código QR si está disponible
        if 'qr_imagen_url' in result:
            print(f"\n📱 QR Image: {result['qr_imagen_url']}")
        
        return result
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


def procesar_pago_paypal(venta_id, monto, notas=""):
    """
    Procesa un pago con PayPal
    """
    
    payload = {
        "venta_id": venta_id,
        "monto": float(monto),
        "metodo_pago": "paypal",
        "notas": notas
    }
    
    print("\n📋 Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/sales/pagos/procesar/",
            headers=headers,
            json=payload
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        print("📊 Response:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json()
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


def obtener_pagos():
    """
    Obtiene la lista de todos los pagos
    """
    
    try:
        response = requests.get(
            f"{BASE_URL}/sales/pagos/",
            headers=headers
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        print("📊 Pagos:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json()
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


def obtener_pago(pago_id):
    """
    Obtiene detalles de un pago específico
    """
    
    try:
        response = requests.get(
            f"{BASE_URL}/sales/pagos/{pago_id}/",
            headers=headers
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        print("📊 Pago:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json()
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


if __name__ == "__main__":
    print("=" * 80)
    print("🛒 Smart Sales 360 - Ejemplos de CU13 (Procesar Pago)")
    print("=" * 80)
    
    # ⚠️ Reemplaza estos valores con datos reales de tu sistema
    venta_id = "123e4567-e89b-12d3-a456-426614174000"  # UUID real de una venta
    
    print("\n" + "=" * 80)
    print("📌 EJEMPLO 1: Procesar pago con tarjeta de crédito (VISA)")
    print("=" * 80)
    procesar_pago_tarjeta(
        venta_id=venta_id,
        monto=150.00,
        tarjeta_numero="4242424242424242",  # Tarjeta de prueba VISA
        tarjeta_nombre="Juan Perez",
        tarjeta_expiracion="12/25",
        tarjeta_cvv="123",
        notas="Pago de prueba con tarjeta VISA"
    )
    
    print("\n" + "=" * 80)
    print("📌 EJEMPLO 2: Procesar pago con tarjeta rechazada")
    print("=" * 80)
    procesar_pago_tarjeta(
        venta_id=venta_id,
        monto=50.00,
        tarjeta_numero="4000000000000002",  # Tarjeta de prueba que será rechazada
        tarjeta_nombre="Test Decline",
        tarjeta_expiracion="12/25",
        tarjeta_cvv="123",
        notas="Prueba de tarjeta rechazada"
    )
    
    print("\n" + "=" * 80)
    print("📌 EJEMPLO 3: Procesar pago con QR")
    print("=" * 80)
    procesar_pago_qr(
        venta_id=venta_id,
        monto=200.00,
        notas="Pago con código QR"
    )
    
    print("\n" + "=" * 80)
    print("📌 EJEMPLO 4: Procesar pago con PayPal")
    print("=" * 80)
    procesar_pago_paypal(
        venta_id=venta_id,
        monto=300.00,
        notas="Pago con PayPal"
    )
    
    print("\n" + "=" * 80)
    print("📌 EJEMPLO 5: Obtener todos los pagos")
    print("=" * 80)
    obtener_pagos()
    
    print("\n" + "=" * 80)
    print("✅ Ejemplos completados")
    print("=" * 80)
