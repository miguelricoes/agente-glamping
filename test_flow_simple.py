#!/usr/bin/env python3
"""
Test simple del flujo - sin emojis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fallback_service import detect_topic_and_provide_fallback

def test_flow(message):
    """Test simple del flujo"""
    
    print(f"TEST: '{message}'")
    
    user_state = {"current_flow": "none"}
    
    handled, response, topic = detect_topic_and_provide_fallback(message)
    
    if handled and user_state.get("current_flow") == "none":
        print(f"RESULTADO: TOPIC FALLBACK EJECUTADO - {topic}")
        print(f"RESPUESTA: {len(response)} caracteres")
        return True
    else:
        print(f"RESULTADO: CONTINUA A LLM")
        return False

def main():
    queries = [
        "que servicios incluyen",
        "politicas de cancelacion", 
        "donde estan ubicados",
        "que actividades hay",
        "tienen piscina",
        "hola como estas"
    ]
    
    success_count = 0
    
    for query in queries:
        if test_flow(query):
            success_count += 1
        print("-" * 40)
    
    print(f"\nRESUMEN: {success_count}/{len(queries)} consultas manejadas sin LLM")

if __name__ == "__main__":
    main()