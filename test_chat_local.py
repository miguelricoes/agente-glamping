#!/usr/bin/env python3
# Script para probar chat_local.py automáticamente

import subprocess
import time
import requests
import sys

def test_server_endpoint():
    """Probar que el servidor esté funcionando"""
    try:
        response = requests.get("http://127.0.0.1:8080/", timeout=5)
        print(f"* Servidor funcionando: {response.status_code}")
        return True
    except Exception as e:
        print(f"* Servidor no responde: {e}")
        return False

def test_chat_endpoint():
    """Probar endpoint /chat"""
    try:
        payload = {"input": "Hola"}
        response = requests.post("http://127.0.0.1:8080/chat", json=payload, timeout=10)
        data = response.json()
        
        if "response" in data and "session_id" in data:
            print("* Endpoint /chat funcionando correctamente")
            print(f"   Respuesta: {data['response'][:100]}...")
            return True
        else:
            print("* Respuesta del endpoint /chat invalida")
            return False
    except Exception as e:
        print(f"* Error en endpoint /chat: {e}")
        return False

def main():
    print("* PROBANDO FUNCIONAMIENTO LOCAL")
    print("=" * 50)
    
    # Esperar un momento para que el servidor esté listo
    print("* Esperando que el servidor este listo...")
    time.sleep(2)
    
    # Probar servidor básico
    if not test_server_endpoint():
        return False
    
    # Probar endpoint de chat
    if not test_chat_endpoint():
        return False
    
    print("\n* TODOS LOS TESTS PASARON")
    print("\n* INSTRUCCIONES DE USO:")
    print("1. Para ejecutar el servidor: python agente_standalone.py")
    print("2. Para chat local: python chat_local.py")
    print("3. Para acceder via web: http://127.0.0.1:8080")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)