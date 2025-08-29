#!/usr/bin/env python3
"""
Test simulado del flujo de WhatsApp para verificar que los servicios se ejecutan
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fallback_service import detect_topic_and_provide_fallback

def simulate_whatsapp_flow(message):
    """Simula el flujo de WhatsApp con el nuevo código"""
    
    print(f"=== SIMULANDO FLUJO WHATSAPP ===")
    print(f"MENSAJE: '{message}'")
    
    # Simular user_state
    user_state = {"current_flow": "none"}
    
    # Paso 1: Otros handlers (simulados como no manejados)
    print("PASO 1: Procesando otros handlers...")
    print("- Greeting: NO")
    print("- Menu selection: NO") 
    print("- Reservation flow: NO")
    print("- Website link: NO")
    print("- Admin contact: NO")
    
    # Paso 2: NUEVO - Topic fallback ANTES de LLM
    print(f"\nPASO 2: TOPIC FALLBACK")
    print(f"Checking topic fallback: current_flow = {user_state.get('current_flow')}")
    
    handled_topic_fallback, topic_fallback_response, detected_topic = detect_topic_and_provide_fallback(message)
    
    print(f"Topic fallback result: handled = {handled_topic_fallback}, topic = {detected_topic}")
    
    if handled_topic_fallback and user_state.get("current_flow") == "none":
        print(f"✅ EJECUTANDO TOPIC FALLBACK SIN LLM: {detected_topic}")
        print(f"RESPUESTA ENVIADA: {len(topic_fallback_response)} caracteres")
        print(f"PREVIEW: {topic_fallback_response[:100]}...")
        return "TOPIC_FALLBACK_SUCCESS"
    else:
        print(f"❌ TOPIC FALLBACK NO EJECUTADO")
        print("CONTINUANDO A LLM...")
        return "WOULD_USE_LLM"

def test_service_queries():
    """Test con consultas de servicios"""
    
    queries = [
        "qué servicios incluyen?",
        "políticas de cancelación", 
        "dónde están ubicados?",
        "qué actividades hay?",
        "tienen piscina?",  # Servicio inexistente
        "hola como estas"   # Debe ir a LLM
    ]
    
    for query in queries:
        result = simulate_whatsapp_flow(query)
        print(f"RESULTADO: {result}")
        print("-" * 60)

if __name__ == "__main__":
    test_service_queries()