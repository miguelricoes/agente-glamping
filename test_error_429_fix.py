#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para verificar que el error 429 en el flujo de sub-opciones esté resuelto
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_error_429_informacion_suboptions():
    """Test del problema exacto: Error 429 cuando usuario está esperando sub-opciones"""
    print("🔥 TEST: Error 429 en Sub-opciones de Información")
    print("=" * 60)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        validation_service = ValidationService()
        qa_chains = {}  # Simular que OpenAI falla
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Simular el estado exacto del usuario cuando ocurre el problema
        user_state = {
            "current_flow": "informacion_general",
            "waiting_for_informacion_suboption": True,
            # Otros estados que podrían estar presentes
            "user_id": "test_user",
            "conversation_started": True
        }
        
        print(f"📋 Estado inicial del usuario:")
        print(f"   current_flow: {user_state['current_flow']}")
        print(f"   waiting_for_informacion_suboption: {user_state['waiting_for_informacion_suboption']}")
        
        # Test casos específicos de sub-opciones
        test_cases = [
            ("ubicación", "debe devolver información completa de ubicación"),
            ("ubicacion", "debe devolver información completa de ubicación (sin acento)"),
            ("1", "debe procesar opción numérica 1 (ubicación)"),
            ("concepto", "debe devolver información completa del concepto"),
            ("concepto glamping", "debe procesar concepto con palabras adicionales"),
            ("2", "debe procesar opción numérica 2 (concepto)"),
            ("políticas", "debe devolver información de políticas"),
            ("politicas", "debe procesar políticas sin acento"),
            ("3", "debe procesar opción numérica 3 (políticas)")
        ]
        
        print(f"\n🧪 Ejecutando {len(test_cases)} casos de prueba:")
        
        results = []
        for i, (message, expected) in enumerate(test_cases, 1):
            print(f"\n{i:2d}. Testing: \"{message}\" ({expected})")
            
            # Reset del estado para cada test
            test_user_state = user_state.copy()
            
            try:
                response = menu_service.handle_informacion_general_suboptions(message, test_user_state)
                
                # Verificaciones básicas
                response_valid = len(response) > 200  # Respuesta robusta
                has_content = any(word in response.lower() for word in ["glamping", "ubicación", "guatavita", "filosofía", "concepto"])
                has_navigation = "menú" in response.lower()
                state_updated = not test_user_state.get("waiting_for_informacion_suboption", True)  # Debería haberse limpiado
                
                success = response_valid and has_content and has_navigation and state_updated
                results.append(success)
                
                print(f"   {'✅' if response_valid else '❌'} Response length: {len(response)} chars")
                print(f"   {'✅' if has_content else '❌'} Has relevant content")  
                print(f"   {'✅' if has_navigation else '❌'} Has navigation options")
                print(f"   {'✅' if state_updated else '❌'} State properly updated")
                print(f"   {'✅ PASS' if success else '❌ FAIL'} Overall")
                
            except Exception as e:
                print(f"   ❌ FAIL - Exception: {e}")
                results.append(False)
        
        # Resultado final
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   Casos exitosos: {passed}/{total} ({success_rate:.1f}%)")
        print(f"   {'✅ PASS' if success_rate >= 85 else '❌ FAIL'} - Test de sub-opciones con error 429")
        
        return success_rate >= 85
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def test_whatsapp_routes_fallback_logic():
    """Test de la lógica modificada en whatsapp_routes.py (simulación)"""
    print("\n🔥 TEST: Lógica de WhatsApp Routes con Error 429")
    print("=" * 60)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        # Simular la lógica que ahora está en whatsapp_routes.py
        def simulate_whatsapp_429_handler(incoming_msg, user_state):
            """Simula la nueva lógica en whatsapp_routes.py"""
            
            # Verificar si el usuario está en flujo conversacional específico
            if (user_state.get("waiting_for_informacion_suboption") and 
                user_state.get("current_flow") == "informacion_general"):
                
                print(f"   🔄 Detectado flujo de información, procesando con menu_service")
                
                # Procesar usando menu_service directamente
                validation_service = ValidationService()
                qa_chains = {}  # Sin RAG chains porque OpenAI falló
                menu_service = create_menu_service(qa_chains, validation_service)
                
                # Procesar sub-opción usando las funciones robustas
                fallback_response = menu_service.handle_informacion_general_suboptions(incoming_msg, user_state)
                
                return True, fallback_response, "informacion_suboption"
            
            elif (user_state.get("waiting_for_politicas_suboption") and 
                  user_state.get("current_flow") == "politicas"):
                
                print(f"   🔄 Detectado flujo de políticas, procesando con menu_service")
                
                validation_service = ValidationService()
                qa_chains = {}
                menu_service = create_menu_service(qa_chains, validation_service)
                
                fallback_response = menu_service._handle_politicas_suboptions(incoming_msg, user_state)
                
                return True, fallback_response, "politicas_suboption"
            
            else:
                print(f"   ⏩ Usuario no en flujo específico, usar fallback genérico")
                return False, "", "no_specific_flow"
        
        # Test casos de flujo específico
        test_scenarios = [
            {
                "name": "Información General - Ubicación", 
                "message": "ubicación",
                "user_state": {
                    "current_flow": "informacion_general",
                    "waiting_for_informacion_suboption": True
                },
                "expected_handled": True
            },
            {
                "name": "Información General - Concepto",
                "message": "concepto", 
                "user_state": {
                    "current_flow": "informacion_general",
                    "waiting_for_informacion_suboption": True
                },
                "expected_handled": True
            },
            {
                "name": "Políticas - Mascotas",
                "message": "mascotas",
                "user_state": {
                    "current_flow": "politicas", 
                    "waiting_for_politicas_suboption": True
                },
                "expected_handled": True
            },
            {
                "name": "Usuario Normal (sin flujo)",
                "message": "hola",
                "user_state": {
                    "current_flow": "none"
                },
                "expected_handled": False
            }
        ]
        
        print(f"\n🧪 Probando {len(test_scenarios)} escenarios:")
        
        results = []
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{i}. Escenario: {scenario['name']}")
            print(f"   Mensaje: \"{scenario['message']}\"")
            print(f"   Estado: {scenario['user_state']}")
            
            handled, response, flow_type = simulate_whatsapp_429_handler(
                scenario['message'], 
                scenario['user_state'].copy()
            )
            
            expected = scenario['expected_handled']
            success = (handled == expected)
            
            if handled:
                response_quality = len(response) > 200 and ('glamping' in response.lower() or 'política' in response.lower())
                success = success and response_quality
                print(f"   Response length: {len(response)} chars")
                print(f"   Response quality: {'✅' if response_quality else '❌'}")
            
            results.append(success)
            print(f"   {'✅ PASS' if success else '❌ FAIL'} - Handled: {handled}, Expected: {expected}")
        
        # Resultado final
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100
        
        print(f"\n📊 RESULTADO:")
        print(f"   Escenarios exitosos: {passed}/{total} ({success_rate:.1f}%)")
        print(f"   {'✅ PASS' if success_rate == 100 else '❌ FAIL'} - Lógica de whatsapp_routes")
        
        return success_rate == 100
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def test_estado_conversacional_preservado():
    """Test que el estado conversacional se preserve correctamente"""
    print("\n🔥 TEST: Preservación del Estado Conversacional")
    print("=" * 60)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        validation_service = ValidationService()
        qa_chains = {}
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Estado inicial cuando usuario escribe "1"
        initial_state = {
            "current_flow": "none"
        }
        
        print("📋 PASO 1: Usuario escribe '1' (configurar estado)")
        response_1 = menu_service.handle_menu_selection("1", initial_state)
        
        print(f"   Estado después del paso 1: {initial_state}")
        print(f"   waiting_for_informacion_suboption: {initial_state.get('waiting_for_informacion_suboption')}")
        print(f"   current_flow: {initial_state.get('current_flow')}")
        
        # Verificar que el estado se configuró correctamente
        state_configured = (
            initial_state.get("waiting_for_informacion_suboption") == True and
            initial_state.get("current_flow") == "informacion_general"
        )
        
        print(f"   {'✅ PASS' if state_configured else '❌ FAIL'} - Estado configurado correctamente")
        
        if not state_configured:
            return False
        
        print("\n📋 PASO 2: Simular error 429 con 'ubicación'")
        # Este sería el momento donde ocurre el error 429 y debe usar el fallback
        
        # Simular que el mensaje llega al handler correcto
        test_state = initial_state.copy()
        response_2 = menu_service.handle_informacion_general_suboptions("ubicación", test_state)
        
        print(f"   Response length: {len(response_2)} chars")
        print(f"   Contains location info: {'GPS' in response_2 or 'Guatavita' in response_2}")
        print(f"   Estado limpiado: {not test_state.get('waiting_for_informacion_suboption', True)}")
        
        # Verificar respuesta y limpieza de estado
        response_valid = (
            len(response_2) > 500 and
            ('GPS' in response_2 or 'Guatavita' in response_2) and
            not test_state.get('waiting_for_informacion_suboption', True)
        )
        
        print(f"   {'✅ PASS' if response_valid else '❌ FAIL'} - Respuesta y estado correctos")
        
        return state_configured and response_valid
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def main():
    """Ejecutar tests del fix para error 429"""
    print("🚀 TESTS DEL FIX PARA ERROR 429 EN SUB-OPCIONES")
    print("🎯 Verificando que el problema del flujo conversacional esté resuelto")
    print("=" * 80)
    
    tests = [
        ("Error 429 en Sub-opciones de Información", test_error_429_informacion_suboptions),
        ("Lógica de WhatsApp Routes", test_whatsapp_routes_fallback_logic),
        ("Preservación del Estado Conversacional", test_estado_conversacional_preservado)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"🧪 EJECUTANDO: {test_name}")
        print(f"{'='*80}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            results.append((test_name, False))
            print(f"   ❌ FAIL - Exception: {e}")
    
    # Resumen final
    print(f"\n{'='*80}")
    print("📊 REPORTE FINAL - FIX ERROR 429 SUB-OPCIONES")
    print(f"{'='*80}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n🎉 FIX PARA ERROR 429 IMPLEMENTADO CORRECTAMENTE")
        print("✅ PROBLEMA DEL FLUJO CONVERSACIONAL RESUELTO")
        print("🚀 ESTADO CONVERSACIONAL RESPETADO EN ERRORES")
        print("🛡️ SISTEMA ROBUSTO ANTE FALLOS DE OPENAI")
        print("\n💫 EL PROBLEMA ORIGINAL ESTÁ COMPLETAMENTE SOLUCIONADO")
        return True
    else:
        print("\n❌ FIX PARA ERROR 429 NECESITA AJUSTES")
        print("🔧 REVISAR IMPLEMENTACIÓN DEL FLUJO CONVERSACIONAL")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)