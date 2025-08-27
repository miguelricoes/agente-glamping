#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del flujo completo esperado: Usuario "1" → "Ubicación" → "Concepto"
Verificar que los resultados esperados estén correctos
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flujo_completo_esperado():
    """Test del flujo exacto especificado en los resultados esperados"""
    print("🔥 TEST: Flujo Completo Esperado")
    print("🎯 Usuario: '1' → 'Ubicación' → 'Concepto'")
    print("=" * 70)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        validation_service = ValidationService()
        qa_chains = {}  # Simular que OpenAI falla (error 429)
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # PASO 1: Usuario escribe "1"
        print("📋 PASO 1: Usuario escribe '1'")
        user_state = {"current_flow": "none"}
        response_1 = menu_service.handle_menu_selection("1", user_state)
        
        # Verificar que se configuró el estado correctamente
        step1_success = (
            user_state.get("waiting_for_informacion_suboption") == True and
            user_state.get("current_flow") == "informacion_general" and
            len(response_1) > 200 and
            "ubicación" in response_1.lower() and
            "concepto" in response_1.lower()
        )
        
        print(f"   Response length: {len(response_1)} chars")
        print(f"   Estado configurado: waiting_for_informacion_suboption = {user_state.get('waiting_for_informacion_suboption')}")
        print(f"   Flujo configurado: current_flow = {user_state.get('current_flow')}")
        print(f"   Contiene 'ubicación': {'✅' if 'ubicación' in response_1.lower() else '❌'}")
        print(f"   Contiene 'concepto': {'✅' if 'concepto' in response_1.lower() else '❌'}")
        print(f"   {'✅ PASO 1 CORRECTO' if step1_success else '❌ PASO 1 FALLO'}")
        
        if not step1_success:
            return False
            
        # PASO 2: Usuario escribe "Ubicación" (simulando error 429)
        print(f"\n📋 PASO 2: Usuario escribe 'Ubicación' (Error 429 simulado)")
        
        # Simular que estamos en whatsapp_routes.py con error 429
        # y verificar la nueva lógica implementada
        if (user_state.get("waiting_for_informacion_suboption") and
            user_state.get("current_flow") == "informacion_general"):
            
            print("   🔄 Sistema detecta estado conversacional correcto")
            print("   🔄 Procesando sub-opción con menu_service directamente")
            
            response_2 = menu_service.handle_informacion_general_suboptions("Ubicación", user_state)
            
            step2_success = (
                len(response_2) > 800 and  # Información completa
                ("GPS" in response_2 or "Guatavita" in response_2) and
                "WhatsApp" in response_2 and
                not user_state.get("waiting_for_informacion_suboption", True)  # Estado limpiado
            )
            
            print(f"   Response length: {len(response_2)} chars")
            print(f"   Contiene ubicación específica: {'✅' if ('GPS' in response_2 or 'Guatavita' in response_2) else '❌'}")
            print(f"   Contiene WhatsApp: {'✅' if 'WhatsApp' in response_2 else '❌'}")
            print(f"   Estado limpiado: {'✅' if not user_state.get('waiting_for_informacion_suboption', True) else '❌'}")
            print(f"   {'✅ PASO 2 CORRECTO' if step2_success else '❌ PASO 2 FALLO'}")
            
        else:
            print("   ❌ Sistema NO detecta estado conversacional")
            step2_success = False
            
        if not step2_success:
            return False
            
        # PASO 3: Resetear estado y probar "Concepto"
        print(f"\n📋 PASO 3: Usuario escribe 'Concepto' (Error 429 simulado)")
        
        # Simular que el usuario vuelve a escribir "1" y luego "concepto"
        user_state_reset = {"current_flow": "none"}
        menu_service.handle_menu_selection("1", user_state_reset)  # Configurar estado otra vez
        
        if (user_state_reset.get("waiting_for_informacion_suboption") and
            user_state_reset.get("current_flow") == "informacion_general"):
            
            print("   🔄 Sistema detecta estado conversacional correcto")
            print("   🔄 Procesando sub-opción con menu_service directamente")
            
            response_3 = menu_service.handle_informacion_general_suboptions("Concepto", user_state_reset)
            
            step3_success = (
                len(response_3) > 1200 and  # Información completa del concepto
                ("glamping" in response_3.lower() or "filosofía" in response_3.lower()) and
                ("naturaleza" in response_3.lower() or "experiencia" in response_3.lower()) and
                not user_state_reset.get("waiting_for_informacion_suboption", True)  # Estado limpiado
            )
            
            print(f"   Response length: {len(response_3)} chars")
            print(f"   Contiene concepto específico: {'✅' if ('glamping' in response_3.lower() or 'filosofía' in response_3.lower()) else '❌'}")
            print(f"   Contiene naturaleza/experiencia: {'✅' if ('naturaleza' in response_3.lower() or 'experiencia' in response_3.lower()) else '❌'}")
            print(f"   Estado limpiado: {'✅' if not user_state_reset.get('waiting_for_informacion_suboption', True) else '❌'}")
            print(f"   {'✅ PASO 3 CORRECTO' if step3_success else '❌ PASO 3 FALLO'}")
            
        else:
            print("   ❌ Sistema NO detecta estado conversacional")
            step3_success = False
            
        # Resultado final
        overall_success = step1_success and step2_success and step3_success
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   Paso 1 (Usuario '1'): {'✅ PASS' if step1_success else '❌ FAIL'}")
        print(f"   Paso 2 (Usuario 'Ubicación' + Error 429): {'✅ PASS' if step2_success else '❌ FAIL'}")
        print(f"   Paso 3 (Usuario 'Concepto' + Error 429): {'✅ PASS' if step3_success else '❌ FAIL'}")
        print(f"   {'✅ FLUJO COMPLETO CORRECTO' if overall_success else '❌ FLUJO NECESITA AJUSTES'}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar verificación del flujo completo esperado"""
    print("🚀 VERIFICACIÓN FLUJO COMPLETO ESPERADO")
    print("🎯 Confirmar que los resultados esperados son correctos")
    print("=" * 80)
    
    success = test_flujo_completo_esperado()
    
    if success:
        print("\n🎉 RESULTADOS ESPERADOS COMPLETAMENTE CORRECTOS")
        print("✅ Paso 1: Usuario '1' → Submenú información configurado")
        print("✅ Paso 2: Usuario 'Ubicación' + Error 429 → Información completa ubicación")
        print("✅ Paso 3: Usuario 'Concepto' + Error 429 → Información completa concepto")
        print("✅ Estados conversacionales manejados correctamente")
        print("✅ Sistema resiliente a error 429 en ambos casos")
        print("\n💫 EL FLUJO ESPERADO FUNCIONA PERFECTAMENTE")
    else:
        print("\n❌ RESULTADOS ESPERADOS NECESITAN AJUSTES")
        print("🔧 REVISAR IMPLEMENTACIÓN DEL FLUJO")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)