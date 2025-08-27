#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test mejorado para verificar las correcciones implementadas
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_ubicacion_fallback():
    """Test de la función mejorada handle_ubicacion_info"""
    print("🧪 TEST: Función Enhanced handle_ubicacion_info")
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        # Crear servicios mock sin RAG
        validation_service = ValidationService()
        qa_chains = {}  # Sin RAG chains para forzar fallback
        
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Test de la función mejorada
        response = menu_service.handle_ubicacion_info()
        
        print(f"✅ Response length: {len(response)} chars")
        print(f"✅ Contains GPS coordinates: {'GPS' in response and ('Latitud' in response or 'Longitud' in response)}")
        print(f"✅ Contains detailed directions: {'Autopista Norte' in response or 'Briceño' in response}")
        print(f"✅ Contains recommendations: {'Recomendaciones' in response or 'despeje' in response}")
        print(f"✅ Contains WhatsApp: {'305 461 4926' in response}")
        print(f"✅ Has navigation menu: {'menú' in response.lower()}")
        
        # Verificaciones específicas
        has_gps = 'GPS' in response and ('Latitud' in response or 'Longitud' in response)
        has_detailed_directions = 'Autopista Norte' in response or 'Briceño' in response
        has_recommendations = 'Recomendaciones' in response or 'despeje' in response
        has_whatsapp = '305 461 4926' in response
        has_navigation = 'menú' in response.lower()
        
        success = all([
            len(response) > 500,  # Respuesta robusta
            has_gps,
            has_detailed_directions,
            has_whatsapp,
            has_navigation
        ])
        
        print(f"   {'✅ PASS' if success else '❌ FAIL'}")
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_emergency_response_consistency():
    """Test que la respuesta de emergencia sea consistente con fallback_service"""
    print("\n🧪 TEST: Emergency Response Consistency")
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        from services.fallback_service import detect_topic_and_provide_fallback
        
        validation_service = ValidationService()
        qa_chains = {}
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Obtener respuesta de emergencia del menu_service
        emergency_response = menu_service._get_emergency_ubicacion_response()
        
        # Obtener respuesta del fallback_service
        handled, fallback_response, topic = detect_topic_and_provide_fallback("ubicación dirección donde están")
        
        print(f"✅ Emergency response length: {len(emergency_response)} chars")
        print(f"✅ Fallback service length: {len(fallback_response)} chars")
        print(f"✅ Both contain GPS: {'GPS' in emergency_response and 'GPS' in fallback_response}")
        print(f"✅ Both contain detailed directions: {('Briceño' in emergency_response or 'destapada' in emergency_response) and ('Briceño' in fallback_response or 'destapada' in fallback_response)}")
        print(f"✅ Both contain WhatsApp: {'305 461 4926' in emergency_response and '305 461 4926' in fallback_response}")
        
        # Verificar consistencia de información clave
        both_have_gps = 'GPS' in emergency_response and 'GPS' in fallback_response
        both_have_directions = ('Briceño' in emergency_response or 'destapada' in emergency_response) and ('Briceño' in fallback_response or 'destapada' in fallback_response)
        both_have_whatsapp = '305 461 4926' in emergency_response and '305 461 4926' in fallback_response
        
        success = all([both_have_gps, both_have_directions, both_have_whatsapp])
        
        print(f"   {'✅ PASS' if success else '❌ FAIL'}")
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_generic_response_detection():
    """Test de la función _is_generic_response"""
    print("\n🧪 TEST: Generic Response Detection")
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        validation_service = ValidationService()
        qa_chains = {}
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Test casos genéricos
        generic_responses = [
            "Como asistente AI, no tengo acceso a esa información específica",
            "No puedo proporcionar detalles específicos sobre ubicaciones",
            "Te recomendaría que verifiques directamente con el establecimiento"
        ]
        
        # Test casos específicos
        specific_responses = [
            "Estamos ubicados en Guatavita, Cundinamarca, Colombia",
            "📍 Dirección: Vereda Pueblo Viejo, Km 15 vía Guatavita",
            "Para llegar desde Bogotá, toma la Autopista Norte"
        ]
        
        generic_detected = [menu_service._is_generic_response(resp) for resp in generic_responses]
        specific_detected = [menu_service._is_generic_response(resp) for resp in specific_responses]
        
        print(f"✅ Generic responses detected: {sum(generic_detected)}/{len(generic_responses)}")
        print(f"✅ Specific responses NOT detected as generic: {len(specific_responses) - sum(specific_detected)}/{len(specific_responses)}")
        
        success = (sum(generic_detected) == len(generic_responses) and 
                  sum(specific_detected) == 0)
        
        print(f"   {'✅ PASS' if success else '❌ FAIL'}")
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_full_flow_simulation():
    """Test simulando el flujo completo sin RAG"""
    print("\n🧪 TEST: Full Flow Simulation (No RAG)")
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        validation_service = ValidationService()
        qa_chains = {}  # Sin RAG chains
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Simular el flujo: menú → opción 1 → ubicación
        user_state = {"current_flow": "none"}
        
        # Paso 1: Usuario escribe "1" → debe mostrar submenú
        menu_response = menu_service.handle_menu_selection("1", user_state)
        
        # Paso 2: Usuario escribe "ubicación" → debe usar fallback
        user_state["waiting_for_informacion_suboption"] = True  # Simular estado
        ubicacion_response = menu_service.handle_ubicacion_info()
        
        print(f"✅ Menu response length: {len(menu_response)} chars")
        print(f"✅ Menu shows ubicación option: {'UBICACIÓN' in menu_response}")
        print(f"✅ Ubicación response length: {len(ubicacion_response)} chars")
        print(f"✅ Ubicación has detailed info: {'GPS' in ubicacion_response and 'WhatsApp' in ubicacion_response}")
        print(f"✅ Both responses have navigation: {'menú' in menu_response.lower() and 'menú' in ubicacion_response.lower()}")
        
        success = all([
            len(menu_response) > 100,
            'UBICACIÓN' in menu_response,
            len(ubicacion_response) > 500,
            'GPS' in ubicacion_response,
            'WhatsApp' in ubicacion_response
        ])
        
        print(f"   {'✅ PASS' if success else '❌ FAIL'}")
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecutar todos los tests mejorados"""
    print("🔥 TESTS DE VERIFICACIÓN - ENHANCED FALLBACK")
    print("=" * 60)
    
    tests = [
        ("Enhanced Ubicación Fallback", test_enhanced_ubicacion_fallback),
        ("Emergency Response Consistency", test_emergency_response_consistency), 
        ("Generic Response Detection", test_generic_response_detection),
        ("Full Flow Simulation", test_full_flow_simulation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🚀 Ejecutando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            results.append((test_name, False))
            print(f"   ❌ FAIL - Exception: {e}")
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE TESTS MEJORADOS")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("✅ TODAS LAS MEJORAS IMPLEMENTADAS CORRECTAMENTE")
        print("🚀 SISTEMA LISTO PARA PRODUCCIÓN")
        return True
    else:
        print("❌ ALGUNAS MEJORAS NECESITAN CORRECCIÓN")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)