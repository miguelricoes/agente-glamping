#!/usr/bin/env python3
"""
Test simple para verificar el endpoint /api/reservas
"""

import sys
import os
import json
import requests

def test_api_reservas():
    """Test básico del endpoint /api/reservas"""
    
    # URL base (ajusta según tu configuración)
    base_url = "http://localhost:8080"  # o la URL de Railway si está deployado
    
    print("=== TEST DEL ENDPOINT /api/reservas ===")
    print(f"URL base: {base_url}")
    
    try:
        # Hacer request al endpoint
        response = requests.get(f"{base_url}/api/reservas", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Respuesta exitosa!")
            print(f"📊 Datos recibidos:")
            print(f"   - Success: {data.get('success')}")
            print(f"   - Total reservas: {data.get('total', 0)}")
            
            reservas = data.get('reservas', [])
            if reservas:
                print(f"   - Primera reserva:")
                primera = reservas[0]
                print(f"     * ID: {primera.get('id')}")
                print(f"     * Nombre: {primera.get('nombre')}")
                print(f"     * Domo: {primera.get('domo')}")
                print(f"     * Fecha entrada: {primera.get('fechaEntrada')}")
            else:
                print("   - No hay reservas en la base de datos")
                
            return True
            
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar al servidor")
        print("💡 Asegúrate de que el agente esté corriendo en Railway o localmente")
        return False
        
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        return False

if __name__ == "__main__":
    success = test_api_reservas()
    print(f"\n🎯 RESULTADO: {'ÉXITO' if success else 'FALLO'}")
    sys.exit(0 if success else 1)