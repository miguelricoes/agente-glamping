#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para verificar el manejo de error 429 en conversation_service.py
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_conversation_service_429_fix():
    """Test del fix para error 429 en conversation_service.py"""
    print("🔥 TEST: Fix Error 429 en Conversation Service")
    print("🎯 Verificar manejo de estado conversacional antes de reset")
    print("=" * 70)
    
    try:
        from services.conversation_service import process_ai_agent
        
        # Simular funciones de agente que fallan con error 429
        def mock_initialize_agent_safe(tools, memory, max_retries=3):
            return True, "mock_agent", ""
        
        def mock_run_agent_safe_with_429(agent, user_message, user_id):
            # Simular error 429 de OpenAI
            return False, "", "OpenAI API error: 429 - insufficient_quota exceeded"
        
        def mock_save_user_memory(user_id, memory):
            pass
        
        # Test con usuario en flujo información general
        print("📋 Test 1: Usuario en flujo información general con error 429")
        user_state = {
            "waiting_for_informacion_suboption": True,
            "current_flow": "informacion_general"
        }
        
        response = process_ai_agent(
            "ubicación", 
            memory=[], 
            tools=[], 
            initialize_agent_safe_func=mock_initialize_agent_safe,
            run_agent_safe_func=mock_run_agent_safe_with_429,
            save_user_memory_func=mock_save_user_memory,
            user_id="test_user_429",
            user_state=user_state
        )
        
        # Verificar resultado
        test1_success = (
            len(response) > 500 and  # Respuesta robusta
            ("ubicación" in response.lower() or "GPS" in response or "Guatavita" in response) and
            not user_state.get("waiting_for_informacion_suboption", True)  # Estado limpiado
        )
        
        print(f"   Response length: {len(response)} chars")
        print(f"   Contains location info: {'✅' if ('GPS' in response or 'Guatavita' in response) else '❌'}")
        print(f"   State cleaned: {'✅' if not user_state.get('waiting_for_informacion_suboption', True) else '❌'}")
        print(f"   {'✅ PASS' if test1_success else '❌ FAIL'} Test 1 - Flujo información general")
        
        # Test con usuario NO en flujo específico
        print(f"\n📋 Test 2: Usuario normal (sin flujo específico) con error 429")
        user_state_normal = {
            "current_flow": "none"
        }
        
        response_normal = process_ai_agent(
            "hola que tal", 
            memory=[], 
            tools=[], 
            initialize_agent_safe_func=mock_initialize_agent_safe,
            run_agent_safe_func=mock_run_agent_safe_with_429,
            save_user_memory_func=mock_save_user_memory,
            user_id="test_user_normal",
            user_state=user_state_normal
        )
        
        # Verificar que reciba respuesta de error apropiada
        test2_success = (
            len(response_normal) > 100 and  # Alguna respuesta
            ("Glamping Brillo de Luna" in response_normal or "WhatsApp" in response_normal)
        )
        
        print(f"   Response length: {len(response_normal)} chars")
        print(f"   Contains contact info: {'✅' if 'WhatsApp' in response_normal else '❌'}")
        print(f"   {'✅ PASS' if test2_success else '❌ FAIL'} Test 2 - Usuario normal")
        
        # Test con concepto
        print(f"\n📋 Test 3: Usuario pidiendo concepto con error 429")
        user_state_concepto = {
            "waiting_for_informacion_suboption": True,
            "current_flow": "informacion_general"
        }
        
        response_concepto = process_ai_agent(
            "concepto", 
            memory=[], 
            tools=[], 
            initialize_agent_safe_func=mock_initialize_agent_safe,
            run_agent_safe_func=mock_run_agent_safe_with_429,
            save_user_memory_func=mock_save_user_memory,
            user_id="test_user_concepto",
            user_state=user_state_concepto
        )
        
        test3_success = (
            len(response_concepto) > 1000 and  # Respuesta robusta para concepto
            ("glamping" in response_concepto.lower() or "filosofía" in response_concepto.lower()) and
            not user_state_concepto.get("waiting_for_informacion_suboption", True)
        )
        
        print(f"   Response length: {len(response_concepto)} chars")
        print(f"   Contains concept info: {'✅' if ('glamping' in response_concepto.lower() or 'filosofía' in response_concepto.lower()) else '❌'}")
        print(f"   State cleaned: {'✅' if not user_state_concepto.get('waiting_for_informacion_suboption', True) else '❌'}")
        print(f"   {'✅ PASS' if test3_success else '❌ FAIL'} Test 3 - Concepto con error 429")
        
        # Resultado final
        overall_success = test1_success and test2_success and test3_success
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   Test 1 (Ubicación + Error 429): {'✅ PASS' if test1_success else '❌ FAIL'}")
        print(f"   Test 2 (Usuario normal + Error 429): {'✅ PASS' if test2_success else '❌ FAIL'}")
        print(f"   Test 3 (Concepto + Error 429): {'✅ PASS' if test3_success else '❌ FAIL'}")
        print(f"   {'✅ FIX CONVERSATION SERVICE FUNCIONAL' if overall_success else '❌ FIX NECESITA AJUSTES'}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar test del fix en conversation service"""
    print("🚀 TEST FIX ERROR 429 EN CONVERSATION SERVICE")
    print("🎯 Verificar que el estado conversacional se maneje ANTES de resetearlo")
    print("=" * 80)
    
    success = test_conversation_service_429_fix()
    
    if success:
        print("\n🎉 FIX EN CONVERSATION SERVICE IMPLEMENTADO CORRECTAMENTE")
        print("✅ Estado conversacional manejado antes de reset")
        print("✅ Sub-opciones procesadas durante error 429")
        print("✅ Información completa entregada incluso con fallos de OpenAI")
        print("✅ Fallback específico activado cuando corresponde")
        print("\n💫 PROBLEMA REAL FINALMENTE SOLUCIONADO")
    else:
        print("\n❌ FIX EN CONVERSATION SERVICE NECESITA AJUSTES")
        print("🔧 REVISAR IMPLEMENTACIÓN DE MANEJO DE ESTADO")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)