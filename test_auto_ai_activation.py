#!/usr/bin/env python3
"""
Test para verificar si detect_auto_ai_activation intercepta consultas de servicios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.validation_service import ValidationService

def test_auto_ai_activation():
    """Test si detect_auto_ai_activation intercepta consultas de servicios"""
    
    validation_service = ValidationService()
    
    consultas_servicios = [
        "que servicios incluyen",
        "servicios incluidos", 
        "que servicios tienen",
        "servicios disponibles",
        "cuales son los servicios",
        "informacion sobre servicios"
    ]
    
    print("TESTING AUTO-AI-ACTIVATION INTERCEPTING SERVICES")
    print("=" * 60)
    
    for consulta in consultas_servicios:
        print(f"\nTEST: '{consulta}'")
        
        should_auto_activate, trigger_type, rag_context = validation_service.detect_auto_ai_activation(consulta)
        
        if should_auto_activate:
            print(f"INTERCEPTADO POR AUTO-AI: {trigger_type} - {rag_context}")
            print("   PROBLEMA: Auto-AI activation bloquea topic fallback")
        else:
            print("NO INTERCEPTADO - Consulta puede pasar al topic fallback")

if __name__ == "__main__":
    test_auto_ai_activation()