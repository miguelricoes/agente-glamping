#!/usr/bin/env python3
"""
Test simple de servicios fallback - sin emojis para Windows
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fallback_service import detect_topic_and_provide_fallback, get_available_topics

def test_service_detection():
    """Test básico de detección de servicios"""
    
    print("TESTING DE DETECCIÓN DE SERVICIOS")
    print("=" * 50)
    
    test_cases = [
        ("tienen yate?", "servicio_inexistente"),
        ("donde están ubicados?", "ubicacion"), 
        ("políticas de cancelación", "politicas"),
        ("qué es glamping?", "concepto"),
        ("qué servicios incluyen?", "servicios"),
        ("qué actividades hay?", "actividades"),
        ("Juan Pérez correo juan@email.com", None),  # Debería ser ignorado
        ("hola cómo estás", None)  # No debería detectar tema
    ]
    
    for message, expected_topic in test_cases:
        print(f"\nTEST: '{message}'")
        
        handled, response, topic = detect_topic_and_provide_fallback(message)
        
        if handled:
            print(f"DETECTADO: {topic}")
            print(f"RESPUESTA: {len(response)} caracteres")
            
            if expected_topic:
                if topic == expected_topic:
                    print("RESULTADO: CORRECTO")
                else:
                    print(f"RESULTADO: ERROR - Esperaba {expected_topic}, obtuvo {topic}")
            else:
                print("RESULTADO: DETECTADO cuando no debería")
        else:
            print("NO DETECTADO")
            if expected_topic:
                print(f"RESULTADO: ERROR - Debería haber detectado {expected_topic}")
            else:
                print("RESULTADO: CORRECTO")
    
    print(f"\nTEMAS DISPONIBLES: {get_available_topics()}")

def test_reservation_protection():
    """Test de protección de datos de reserva"""
    
    print("\n\nTESTING DE PROTECCIÓN DE RESERVA")
    print("=" * 50)
    
    reservation_data = [
        "Juan Pérez, correo juan@email.com, teléfono 3001234567",
        "2 huéspedes, entrada 15/12/2024, salida 17/12/2024", 
        "domo Antares, pago efectivo, servicios masajes",
        "reserva para María email maria@test.com"
    ]
    
    for data in reservation_data:
        handled, response, topic = detect_topic_and_provide_fallback(data)
        
        print(f"\nDATA: '{data[:40]}...'")
        if not handled:
            print("PROTEGIDO: Datos de reserva no interceptados")
        else:
            print(f"INTERCEPTADO: {topic} - REVISAR")

if __name__ == "__main__":
    test_service_detection()
    test_reservation_protection()
    print("\nTESTING COMPLETADO")