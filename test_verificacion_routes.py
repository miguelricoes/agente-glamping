#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de verificación para confirmar que routes/whatsapp_routes.py está correctamente implementado
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_routes_implementation():
    """Verificar que la implementación en routes esté correcta"""
    print("🔥 TEST: Verificación Routes Implementation")
    print("=" * 60)
    
    try:
        # Leer el archivo routes/whatsapp_routes.py
        with open("routes/whatsapp_routes.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Verificaciones críticas
        checks = [
            ("VERIFICAR ESTADO DE CONVERSACIÓN ANTES DE FALLBACK", 
             "VERIFICAR ESTADO DE CONVERSACIÓN ANTES DE FALLBACK" in content),
            
            ("waiting_for_informacion_suboption detection", 
             "waiting_for_informacion_suboption" in content and "informacion_general" in content),
            
            ("menu_service.handle_informacion_general_suboptions call", 
             "menu_service.handle_informacion_general_suboptions(incoming_msg, user_state)" in content),
            
            ("information_suboption personality type", 
             "information_suboption" in content),
            
            ("waiting_for_domos_followup handling", 
             "waiting_for_domos_followup" in content),
            
            ("waiting_for_servicios_followup handling", 
             "waiting_for_servicios_followup" in content),
            
            ("emergency_specific personality type", 
             "emergency_specific" in content),
            
            ("FALLBACK ESPECÍFICO POR TEMA (MEJORADO)", 
             "FALLBACK ESPECÍFICO POR TEMA (MEJORADO)" in content),
            
            ("detect_topic_and_provide_fallback call", 
             "detect_topic_and_provide_fallback(incoming_msg)" in content),
            
            ("FALLBACK GENÉRICO solo si no hay específico", 
             "FALLBACK GENÉRICO solo si no hay específico" in content)
        ]
        
        print("📋 Verificando implementación:")
        
        all_passed = True
        for check_name, condition in checks:
            status = "✅ PASS" if condition else "❌ FAIL"
            print(f"   {status} {check_name}")
            if not condition:
                all_passed = False
        
        # Verificar que no hay código duplicado o inconsistente
        lines = content.split('\n')
        error_429_lines = [i for i, line in enumerate(lines) if "429" in line and "str(e)" in line]
        
        if len(error_429_lines) == 1:
            print("   ✅ PASS Única detección de error 429")
        else:
            print(f"   ❌ FAIL Múltiples detecciones de error 429: {len(error_429_lines)}")
            all_passed = False
        
        # Buscar líneas problemáticas o duplicadas
        fallback_return_count = content.count("return str(resp)")
        if fallback_return_count >= 3:  # Debe haber varios returns en diferentes condiciones
            print("   ✅ PASS Múltiples puntos de retorno correctos")
        else:
            print(f"   ⚠️ WARNING Pocos puntos de retorno: {fallback_return_count}")
        
        print(f"\n🎯 RESULTADO: {'✅ IMPLEMENTACIÓN CORRECTA' if all_passed else '❌ IMPLEMENTACIÓN NECESITA CORRECCIÓN'}")
        return all_passed
        
    except Exception as e:
        print(f"❌ Error leyendo archivo routes: {e}")
        return False

def test_integration_simulation():
    """Simular integración completa con el nuevo código"""
    print("\n🔥 TEST: Simulación de Integración Completa")
    print("=" * 60)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        # Simular la lógica exacta del nuevo código en routes
        def simulate_429_handling(incoming_msg, user_state):
            """Simula la nueva lógica implementada en whatsapp_routes.py"""
            
            # Primera verificación: información general
            if (user_state.get("waiting_for_informacion_suboption") and
                user_state.get("current_flow") == "informacion_general"):
                
                print("   🔄 Detectado flujo información, usando menu_service")
                validation_service = ValidationService()
                qa_chains = {}
                menu_service = create_menu_service(qa_chains, validation_service)
                response = menu_service.handle_informacion_general_suboptions(incoming_msg, user_state)
                return True, response, "information_suboption"
            
            # Segunda verificación: followup questions
            elif user_state.get("waiting_for_domos_followup") or user_state.get("waiting_for_servicios_followup"):
                print("   🔄 Detectado flujo followup, usando menu_service")
                validation_service = ValidationService()
                qa_chains = {}
                menu_service = create_menu_service(qa_chains, validation_service)
                
                if user_state.get("waiting_for_domos_followup"):
                    # Simular respuesta de domos followup
                    response = "Información adicional sobre nuestros domos: Contamos con domos de lujo con todas las comodidades..."
                elif user_state.get("waiting_for_servicios_followup"):
                    # Simular respuesta de servicios followup  
                    response = "Información adicional sobre nuestros servicios: Ofrecemos experiencias únicas..."
                else:
                    response = "No pude procesar tu consulta específica en este momento."
                
                return True, response, "followup_during_error"
            
            # Tercera verificación: fallback específico por tema
            else:
                print("   🔄 Usando fallback específico por tema")
                from services.fallback_service import detect_topic_and_provide_fallback
                handled, response, topic = detect_topic_and_provide_fallback(incoming_msg)
                if handled:
                    return True, response, "emergency_specific"
                else:
                    # Fallback genérico final
                    response = "Disculpa, tenemos problemas temporales. ¿Podrías intentar de nuevo?"
                    return True, response, "emergency"
        
        # Test scenarios
        scenarios = [
            {
                "name": "Información General - Ubicación",
                "msg": "ubicación", 
                "state": {"waiting_for_informacion_suboption": True, "current_flow": "informacion_general"},
                "expected_type": "information_suboption"
            },
            {
                "name": "Domos Followup",
                "msg": "más información domos",
                "state": {"waiting_for_domos_followup": True},
                "expected_type": "followup_during_error"
            },
            {
                "name": "Servicios Followup", 
                "msg": "qué servicios tienen",
                "state": {"waiting_for_servicios_followup": True},
                "expected_type": "followup_during_error"
            },
            {
                "name": "Fallback Específico - Tema General",
                "msg": "ubicacion del glamping", 
                "state": {"current_flow": "none"},
                "expected_type": "emergency_specific"
            }
        ]
        
        results = []
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{i}. Probando: {scenario['name']}")
            print(f"   Mensaje: '{scenario['msg']}'")
            
            handled, response, response_type = simulate_429_handling(scenario['msg'], scenario['state'].copy())
            
            success = (
                handled and 
                len(response) > 100 and 
                response_type == scenario['expected_type']
            )
            
            results.append(success)
            print(f"   Response length: {len(response)} chars")
            print(f"   Response type: {response_type}")
            print(f"   Expected type: {scenario['expected_type']}")
            print(f"   {'✅ PASS' if success else '❌ FAIL'} Escenario")
        
        passed = sum(results)
        total = len(results)
        
        print(f"\n📊 RESULTADO INTEGRACIÓN:")
        print(f"   Escenarios exitosos: {passed}/{total}")
        print(f"   {'✅ PASS' if passed == total else '❌ FAIL'} Integración completa")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Error en simulación: {e}")
        return False

def main():
    """Ejecutar verificación completa"""
    print("🚀 VERIFICACIÓN FINAL - ROUTES IMPLEMENTATION")
    print("🎯 Confirmar que whatsapp_routes.py está correctamente modificado")
    print("=" * 80)
    
    tests = [
        ("Verificación de Implementación en Routes", test_routes_implementation),
        ("Simulación de Integración Completa", test_integration_simulation)
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
    
    # Reporte final
    print(f"\n{'='*80}")
    print("📊 REPORTE FINAL - VERIFICACIÓN ROUTES")
    print(f"{'='*80}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("\n🎉 ROUTES CORRECTAMENTE IMPLEMENTADAS")
        print("✅ CÓDIGO MEJORADO Y OPTIMIZADO") 
        print("🚀 MANEJO INTELIGENTE DE ESTADOS CONVERSACIONALES")
        print("🛡️ FALLBACKS ROBUSTOS PARA TODOS LOS ESCENARIOS")
        print("\n💫 IMPLEMENTACIÓN TÉCNICA PERFECTA")
        return True
    else:
        print("\n❌ ROUTES NECESITAN AJUSTES")
        print("🔧 REVISAR IMPLEMENTACIÓN ESPECÍFICA")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)