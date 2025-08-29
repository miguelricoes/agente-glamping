#!/usr/bin/env python3
"""
Test final del flujo completo simulado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fallback_service import detect_topic_and_provide_fallback
from services.validation_service import ValidationService

def simulate_complete_whatsapp_flow(message):
    """Simula el flujo completo de WhatsApp con el nuevo orden"""
    
    print(f"=== FLUJO COMPLETO WHATSAPP ===")
    print(f"MENSAJE: '{message}'")
    print("-" * 40)
    
    user_state = {"current_flow": "none"}
    
    # Paso 1-10: Otros handlers (simulados como NO MANEJADOS)
    print("PASO 1-10: Otros handlers...")
    print("- Greeting: NO")
    print("- Menu: NO") 
    print("- Reservation: NO")
    print("- Website: NO")
    print("- Admin contact: NO")
    print("- Reservation intent: NO")
    
    # Paso 11.5: TOPIC FALLBACK (NUEVA POSICIÓN)
    print(f"\nPASO 11.5: TOPIC FALLBACK (NUEVA POSICIÓN)")
    
    handled_topic_fallback, topic_fallback_response, detected_topic = detect_topic_and_provide_fallback(message)
    
    if handled_topic_fallback and user_state.get("current_flow") == "none":
        print(f"RESULTADO: TOPIC FALLBACK EJECUTADO - {detected_topic}")
        print(f"RESPUESTA: {len(topic_fallback_response)} caracteres")
        print("STATUS: ENVIADO A WHATSAPP ✓")
        return "SUCCESS_TOPIC_FALLBACK"
    else:
        print("RESULTADO: Topic fallback NO ejecutado, continuando...")
    
    # Paso 12: AUTO-AI ACTIVATION (Ahora DESPUÉS del fallback)
    print(f"\nPASO 12: AUTO-AI ACTIVATION") 
    
    validation_service = ValidationService()
    should_auto_activate, trigger_type, rag_context = validation_service.detect_auto_ai_activation(message)
    
    if should_auto_activate:
        print(f"RESULTADO: AUTO-AI ACTIVADO - {trigger_type} - {rag_context}")
        print("STATUS: ENVIADO A LLM")
        return "WOULD_USE_AUTO_AI_LLM"
    else:
        print("RESULTADO: Auto-AI NO activado, continuando...")
    
    # Paso 13: FALLBACK GENERAL LLM
    print(f"\nPASO 13: FALLBACK GENERAL LLM")
    print("STATUS: ENVIADO A LLM GENERAL")
    return "WOULD_USE_GENERAL_LLM"

def test_servicios_flow():
    """Test del flujo con consultas de servicios"""
    
    consultas = [
        "que servicios incluyen",
        "donde estan ubicados", 
        "politicas de cancelacion",
        "que actividades hay",
        "tienen piscina",
        "hola como estas"
    ]
    
    results = {}
    
    for consulta in consultas:
        result = simulate_complete_whatsapp_flow(consulta)
        results[consulta] = result
        print("=" * 60)
    
    print("\n📊 RESUMEN DE RESULTADOS:")
    print("=" * 40)
    
    success_count = 0
    for consulta, result in results.items():
        status = "✅ SIN LLM" if result == "SUCCESS_TOPIC_FALLBACK" else "⚠️  CON LLM"
        print(f"{status} '{consulta}' → {result}")
        if result == "SUCCESS_TOPIC_FALLBACK":
            success_count += 1
    
    print(f"\n🎯 {success_count}/{len(consultas)} consultas manejadas SIN LLM")

if __name__ == "__main__":
    test_servicios_flow()