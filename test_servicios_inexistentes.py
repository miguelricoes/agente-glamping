#!/usr/bin/env python3
"""
Test específico para servicios inexistentes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fallback_service import detect_topic_and_provide_fallback

def test_servicio_inexistente(query):
    print(f"TEST: '{query}'")
    
    handled, response, topic = detect_topic_and_provide_fallback(query)
    
    if handled and topic == "servicio_inexistente":
        print(f"DETECTADO: {topic}")
        print(f"RESPUESTA: {len(response)} caracteres")
        # Buscar si menciona servicios reales
        if "masajes" in response and "senderismo" in response:
            print("CORRECTO: Redirige a servicios reales")
        else:
            print("PROBLEMA: No redirige correctamente")
        return True
    else:
        print("NO DETECTADO")
        return False

def main():
    servicios_inexistentes = [
        "tienen piscina",
        "hay casino",
        "puedo hacer surf", 
        "tienen yate",
        "deportes extremos",
        "buceo disponible"
    ]
    
    for servicio in servicios_inexistentes:
        test_servicio_inexistente(servicio)
        print("-" * 40)

if __name__ == "__main__":
    main()