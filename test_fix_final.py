#!/usr/bin/env python3
"""
Test final para verificar que servicios funciona end-to-end
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.validation_service import ValidationService
from services.fallback_service import detect_topic_and_provide_fallback

def test_servicios_end_to_end():
    """Test end-to-end del flujo de servicios"""
    
    message = "servicios"
    
    print("TEST END-TO-END: 'servicios'")
    print("=" * 40)
    
    # Paso 1: Verificar que NO es interceptado por menu
    validation_service = ValidationService()
    is_menu = validation_service.is_menu_selection(message)
    
    print(f"PASO 1 - Menu interception: {is_menu}")
    if not is_menu:
        print("OK - No interceptado por menu")
    else:
        print("ERROR - Interceptado por menu")
        return
    
    # Paso 2: Verificar que SÍ es manejado por topic fallback
    handled, response, topic = detect_topic_and_provide_fallback(message)
    
    print(f"PASO 2 - Topic fallback: handled={handled}, topic={topic}")
    if handled:
        print(f"OK - Manejado por topic fallback: {topic}")
        print(f"Respuesta: {len(response)} caracteres")
    else:
        print("ERROR - No manejado por topic fallback")
        return
    
    print("\nRESULTADO FINAL: SUCCESS")
    print("El flujo 'servicios' funcionara correctamente en WhatsApp")

def test_multiple_service_queries():
    """Test múltiples consultas de servicios"""
    
    queries = [
        "servicios",
        "que servicios incluyen", 
        "servicios disponibles",
        "informacion sobre servicios"
    ]
    
    validation_service = ValidationService()
    
    print("\nTEST MULTIPLE QUERIES")
    print("=" * 40)
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        
        # Check menu no intercept
        is_menu = validation_service.is_menu_selection(query)
        print(f"Menu: {'NO' if not is_menu else 'SI'}")
        
        # Check topic fallback handles
        handled, response, topic = detect_topic_and_provide_fallback(query)
        print(f"Fallback: {'SI' if handled else 'NO'} - {topic}")
        
        if not is_menu and handled:
            print("STATUS: OK")
        else:
            print("STATUS: PROBLEM")

if __name__ == "__main__":
    test_servicios_end_to_end()
    test_multiple_service_queries()