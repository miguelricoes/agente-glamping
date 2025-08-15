#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test del Menú Principal de Bienvenida
=====================================
Prueba el sistema de menú implementado para WhatsApp
"""

import requests
import json
import uuid

# Configuración
API_URL = "http://127.0.0.1:8080/chat"

def test_menu_system():
    """Prueba el sistema completo de menú"""
    print("TESTING SISTEMA DE MENU PRINCIPAL")
    print("=" * 60)
    
    # Generar session_id único para esta prueba
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    print()
    
    tests = [
        {
            "name": "1. Saludo inicial - Debe mostrar menú",
            "input": "hola",
            "expected_content": ["María", "menu", "1", "2", "3", "4"]
        },
        {
            "name": "2. Opción 1 - Información de Domos",
            "input": "1",
            "expected_content": ["domos", "características"]
        },
        {
            "name": "3. Opción 2 - Servicios",
            "input": "2", 
            "expected_content": ["servicios", "incluidos"]
        },
        {
            "name": "4. Opción 3 - Disponibilidad",
            "input": "3",
            "expected_content": ["disponibilidad", "fechas", "DD/MM/AAAA"]
        },
        {
            "name": "5. Consulta de fechas después de opción 3",
            "input": "15/12/2024 al 17/12/2024, 2 personas",
            "expected_content": ["disponibilidad", "2024"]
        },
        {
            "name": "6. Opción 4 - Información General",
            "input": "4",
            "expected_content": ["información", "ubicación"]
        },
        {
            "name": "7. Selección inválida",
            "input": "5",
            "expected_content": ["no entendí", "1 al 4"]
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(tests, 1):
        print(f"Test {i}: {test['name']}")
        print(f"Input: '{test['input']}'")
        
        try:
            # Hacer petición al API
            response = requests.post(API_URL, json={
                "input": test["input"],
                "session_id": session_id
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "").lower()
                
                print(f"Response: {data.get('response', 'No response')[:200]}...")
                
                # Verificar contenido esperado
                all_found = True
                for expected in test["expected_content"]:
                    if expected.lower() not in response_text:
                        all_found = False
                        print(f"X No encontrado: '{expected}'")
                
                if all_found:
                    print("OK PASADO")
                    passed += 1
                else:
                    print("ERROR FALLIDO - Contenido esperado no encontrado")
                    failed += 1
            else:
                print(f"ERROR FALLIDO - Status: {response.status_code}")
                failed += 1
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR FALLIDO - Error de conexion: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR FALLIDO - Error: {e}")
            failed += 1
        
        print("-" * 50)
    
    print(f"\nRESULTADOS FINALES:")
    print(f"OK Tests exitosos: {passed}")
    print(f"ERROR Tests fallidos: {failed}")
    print(f"Porcentaje de exito: {(passed/(passed+failed)*100):.1f}%")
    
    return passed == len(tests)

if __name__ == "__main__":
    try:
        success = test_menu_system()
        if success:
            print("\nTODOS LOS TESTS PASARON - El menu funciona correctamente!")
        else:
            print("\nALGUNOS TESTS FALLARON - Revisar implementacion")
    except KeyboardInterrupt:
        print("\n\nTests interrumpidos por el usuario")
    except Exception as e:
        print(f"\nError ejecutando tests: {e}")