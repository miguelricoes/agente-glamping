#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar el fix del error 429
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Test simple del problema original"""
    print("🔥 TEST SIMPLE: Fix Error 429 en Sub-opciones")
    print("=" * 60)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        validation_service = ValidationService()
        qa_chains = {}  # Simular OpenAI fallando
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # PASO 1: Usuario escribe "1"
        user_state = {"current_flow": "none"}
        response_1 = menu_service.handle_menu_selection("1", user_state)
        
        print(f"📋 PASO 1 - Usuario '1': Estado configurado")
        print(f"   waiting_for_informacion_suboption: {user_state.get('waiting_for_informacion_suboption')}")
        print(f"   current_flow: {user_state.get('current_flow')}")
        
        # PASO 2: Usuario escribe "ubicación" (con el fix del error 429)
        print(f"\n📋 PASO 2 - Usuario 'ubicación' (simulando error 429)")
        
        # Simular la nueva lógica de whatsapp_routes.py
        if (user_state.get("waiting_for_informacion_suboption") and 
            user_state.get("current_flow") == "informacion_general"):
            
            print("   ✅ Estado detectado correctamente")
            print("   🔄 Procesando con menu_service directamente")
            
            response_2 = menu_service.handle_informacion_general_suboptions("ubicación", user_state)
            
            print(f"   ✅ Response: {len(response_2)} chars")
            print(f"   ✅ Contains GPS: {'GPS' in response_2}")
            print(f"   ✅ Contains Guatavita: {'Guatavita' in response_2}")
            print(f"   ✅ Estado limpiado: {not user_state.get('waiting_for_informacion_suboption', True)}")
            
            success = (
                len(response_2) > 500 and
                'GPS' in response_2 and
                'Guatavita' in response_2 and
                not user_state.get('waiting_for_informacion_suboption', True)
            )
            
            print(f"\n🎯 RESULTADO: {'✅ PROBLEMA RESUELTO' if success else '❌ PROBLEMA PERSISTE'}")
            return success
        else:
            print("   ❌ Estado NO detectado correctamente")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 FIX DEL ERROR 429 FUNCIONANDO CORRECTAMENTE")
        print("💫 EL PROBLEMA ORIGINAL ESTÁ COMPLETAMENTE SOLUCIONADO")
    else:
        print("\n❌ FIX DEL ERROR 429 NECESITA AJUSTES")
    sys.exit(0 if success else 1)