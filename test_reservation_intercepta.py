#!/usr/bin/env python3
"""
Test para verificar si ReservationIntentService intercepta consultas de servicios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.reservation_intent_service import get_reservation_intent_service

def test_reservation_interception():
    """Test si ReservationIntentService intercepta consultas de servicios"""
    
    reservation_service = get_reservation_intent_service()
    
    consultas_servicios = [
        "que servicios incluyen",
        "servicios incluidos", 
        "que servicios tienen",
        "servicios disponibles",
        "cuales son los servicios"
    ]
    
    print("TESTING INTERCEPTACION POR RESERVATIONINTENTSERVICE")
    print("=" * 60)
    
    for consulta in consultas_servicios:
        print(f"\nTEST: '{consulta}'")
        
        # Simular user_state vacío
        user_state = {"current_flow": "none"}
        
        intent_type, action, reason = reservation_service.analyze_reservation_intent(consulta, user_state)
        
        if intent_type != "none":
            print(f"INTERCEPTADO: {intent_type} - {action} - {reason}")
            print("   PROBLEMA: ReservationIntentService bloquea consultas de servicios")
        else:
            print("NO INTERCEPTADO - Consulta puede pasar al fallback")

if __name__ == "__main__":
    test_reservation_interception()