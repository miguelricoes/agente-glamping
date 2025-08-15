#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test del endpoint /chat del agente
"""

import requests
import json

def test_chat_api():
    """Prueba el endpoint /chat directamente"""
    print("=== Test del Endpoint /chat ===\n")
    
    # URL del endpoint
    url = "http://127.0.0.1:8080/chat"
    
    # Test queries
    test_messages = [
        "¿Qué es el glamping?",
        "¿Qué tipos de domos tienen?", 
        "¿Dónde están ubicados?",
        "¿Cuáles son las políticas del glamping?"
    ]
    
    session_id = None
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: {message}")
        
        payload = {"input": message}
        if session_id:
            payload["session_id"] = session_id
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if not session_id:
                    session_id = data.get("session_id")
                    print(f"Session ID: {session_id}")
                
                print(f"Respuesta: {data.get('response', 'No response')}")
                print("OK: Respuesta exitosa")
            else:
                print(f"ERROR: Status {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("ERROR: Timeout - el servidor tomó mucho tiempo")
        except requests.exceptions.ConnectionError:
            print("ERROR: No se pudo conectar al servidor")
            print("HINT: Asegurate de ejecutar 'python agente.py' en otra terminal")
            break
        except Exception as e:
            print(f"ERROR: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_chat_api()