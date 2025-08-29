#!/usr/bin/env python3
"""
Test del contenido de respuestas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fallback_service import detect_topic_and_provide_fallback

def test_response_content():
    
    # Test servicio inexistente
    handled, response, topic = detect_topic_and_provide_fallback("tienen yate")
    
    if handled:
        print("RESPUESTA DE SERVICIO INEXISTENTE:")
        print("=" * 50)
        # Imprimir sin emojis problemáticos
        clean_response = response.encode('ascii', 'ignore').decode('ascii')
        print(clean_response[:500])
        print("=" * 50)
        
        # Verificar contenido
        if "masajes" in response.lower():
            print("CONTIENE: masajes")
        if "senderismo" in response.lower():
            print("CONTIENE: senderismo")
        if "yoga" in response.lower():
            print("CONTIENE: yoga")

def test_servicios_response():
    
    handled, response, topic = detect_topic_and_provide_fallback("que servicios incluyen")
    
    if handled:
        print("\nRESPUESTA DE SERVICIOS:")
        print("=" * 50)
        clean_response = response.encode('ascii', 'ignore').decode('ascii')
        print(clean_response[:500])
        print("=" * 50)

if __name__ == "__main__":
    test_response_content() 
    test_servicios_response()