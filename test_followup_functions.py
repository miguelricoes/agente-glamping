#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para verificar las nuevas funciones de followup
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_followup_functions():
    """Test directo de las funciones de followup"""
    print("🔥 TEST: Funciones de Followup Agregadas")
    print("=" * 60)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        validation_service = ValidationService()
        qa_chains = {}
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Verificar que las funciones existen
        has_domos_followup = hasattr(menu_service, 'handle_domos_followup_question')
        has_servicios_followup = hasattr(menu_service, 'handle_servicios_followup_question')
        
        print(f"📋 Verificación de funciones:")
        print(f"   {'✅ EXISTE' if has_domos_followup else '❌ NO EXISTE'} handle_domos_followup_question")
        print(f"   {'✅ EXISTE' if has_servicios_followup else '❌ NO EXISTE'} handle_servicios_followup_question")
        
        if not has_domos_followup or not has_servicios_followup:
            return False
        
        # Test funcional de las nuevas funciones
        print(f"\n🧪 Testing funciones:")
        
        # Test domos followup
        print(f"\n1. Testing handle_domos_followup_question:")
        user_state_domos = {"waiting_for_domos_followup": True}
        response_domos = menu_service.handle_domos_followup_question("más información", user_state_domos)
        
        domos_success = (
            len(response_domos) > 200 and
            "DOMOS BRILLO DE LUNA" in response_domos and
            "Antares" in response_domos and
            not user_state_domos.get("waiting_for_domos_followup", True)
        )
        
        print(f"   Response length: {len(response_domos)} chars")
        print(f"   Contains domos info: {'✅' if 'DOMOS BRILLO DE LUNA' in response_domos else '❌'}")
        print(f"   Contains Antares: {'✅' if 'Antares' in response_domos else '❌'}")
        print(f"   State reset: {'✅' if not user_state_domos.get('waiting_for_domos_followup', True) else '❌'}")
        print(f"   {'✅ PASS' if domos_success else '❌ FAIL'} Domos followup")
        
        # Test servicios followup
        print(f"\n2. Testing handle_servicios_followup_question:")
        user_state_servicios = {"waiting_for_servicios_followup": True}
        response_servicios = menu_service.handle_servicios_followup_question("qué incluye", user_state_servicios)
        
        servicios_success = (
            len(response_servicios) > 200 and
            "SERVICIOS BRILLO DE LUNA" in response_servicios and
            "INCLUIDOS" in response_servicios and
            not user_state_servicios.get("waiting_for_servicios_followup", True)
        )
        
        print(f"   Response length: {len(response_servicios)} chars")
        print(f"   Contains servicios info: {'✅' if 'SERVICIOS BRILLO DE LUNA' in response_servicios else '❌'}")
        print(f"   Contains incluidos: {'✅' if 'INCLUIDOS' in response_servicios else '❌'}")
        print(f"   State reset: {'✅' if not user_state_servicios.get('waiting_for_servicios_followup', True) else '❌'}")
        print(f"   {'✅ PASS' if servicios_success else '❌ FAIL'} Servicios followup")
        
        overall_success = domos_success and servicios_success
        print(f"\n🎯 RESULTADO: {'✅ FUNCIONES AGREGADAS CORRECTAMENTE' if overall_success else '❌ FUNCIONES NECESITAN AJUSTES'}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecutar test de funciones followup"""
    print("🚀 TEST DE FUNCIONES FOLLOWUP AGREGADAS")
    print("🎯 Verificar que handle_domos_followup_question y handle_servicios_followup_question funcionen")
    print("=" * 80)
    
    success = test_followup_functions()
    
    if success:
        print("\n🎉 FUNCIONES FOLLOWUP IMPLEMENTADAS CORRECTAMENTE")
        print("✅ handle_domos_followup_question - FUNCIONAL")
        print("✅ handle_servicios_followup_question - FUNCIONAL")
        print("✅ Estado conversacional manejado correctamente")
        print("✅ Respuestas robustas con información completa")
        print("\n💫 INTEGRACIÓN CON ROUTES LISTA PARA FUNCIONAR")
    else:
        print("\n❌ FUNCIONES FOLLOWUP NECESITAN CORRECCIÓN")
        print("🔧 REVISAR IMPLEMENTACIÓN EN menu_service.py")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)