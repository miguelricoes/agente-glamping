#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para verificar las mejoras en handle_concepto_info()
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_concepto_enhanced_fallback():
    """Test de la función mejorada handle_concepto_info"""
    print("🧪 TEST: Enhanced handle_concepto_info")
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        # Crear servicios mock sin RAG
        validation_service = ValidationService()
        qa_chains = {}  # Sin RAG chains para forzar fallback
        
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Test de la función mejorada
        response = menu_service.handle_concepto_info()
        
        print(f"✅ Response length: {len(response)} chars")
        print(f"✅ Contains glamping concept: {'glamping' in response.lower()}")
        print(f"✅ Contains philosophy: {'filosofía' in response.lower()}")
        print(f"✅ Contains mission: {'misión' in response.lower()}")
        print(f"✅ Contains website: {'glampingbrillodelaluna.com' in response}")
        print(f"✅ Contains navigation menu: {'menú' in response.lower()}")
        print(f"✅ Contains Guatavita: {'Guatavita' in response}")
        print(f"✅ Contains Tominé: {'Tominé' in response}")
        
        # Verificaciones específicas
        has_glamping_concept = 'glamping' in response.lower()
        has_philosophy = 'filosofía' in response.lower()
        has_mission = 'misión' in response.lower()
        has_website = 'glampingbrillodelaluna.com' in response
        has_navigation = 'menú' in response.lower()
        has_location_info = 'Guatavita' in response
        
        success = all([
            len(response) > 800,  # Respuesta robusta
            has_glamping_concept,
            has_philosophy,
            has_mission,
            has_website,
            has_navigation,
            has_location_info
        ])
        
        print(f"   {'✅ PASS' if success else '❌ FAIL'}")
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_concepto_fallback_consistency():
    """Test que el concepto sea consistente con fallback_service"""
    print("\n🧪 TEST: Concepto Fallback Consistency")
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        from services.fallback_service import detect_topic_and_provide_fallback
        
        validation_service = ValidationService()
        qa_chains = {}
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Obtener respuesta del menu_service
        concepto_response = menu_service.handle_concepto_info()
        
        # Obtener respuesta del fallback_service directamente
        handled, fallback_response, topic = detect_topic_and_provide_fallback("concepto filosofía que es glamping brillo de luna")
        
        print(f"✅ Menu concepto response length: {len(concepto_response)} chars")
        print(f"✅ Fallback service length: {len(fallback_response)} chars")
        print(f"✅ Fallback service handled: {handled}")
        print(f"✅ Both contain glamping: {'glamping' in concepto_response.lower() and 'glamping' in fallback_response.lower()}")
        print(f"✅ Both contain filosofía: {'filosof' in concepto_response.lower() and 'filosof' in fallback_response.lower()}")
        print(f"✅ Both contain Guatavita: {'Guatavita' in concepto_response and 'Guatavita' in fallback_response}")
        
        # Verificar consistencia de información clave
        both_have_glamping = 'glamping' in concepto_response.lower() and 'glamping' in fallback_response.lower()
        both_have_philosophy = 'filosof' in concepto_response.lower() and 'filosof' in fallback_response.lower()
        both_have_location = 'Guatavita' in concepto_response and 'Guatavita' in fallback_response
        fallback_handled = handled
        
        success = all([both_have_glamping, both_have_philosophy, both_have_location, fallback_handled])
        
        print(f"   {'✅ PASS' if success else '❌ FAIL'}")
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_concepto_emergency_response():
    """Test de la respuesta de emergencia actualizada"""
    print("\n🧪 TEST: Concepto Emergency Response")
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        validation_service = ValidationService()
        qa_chains = {}
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Obtener respuesta de emergencia
        emergency_response = menu_service._get_emergency_concepto_response()
        
        print(f"✅ Emergency response length: {len(emergency_response)} chars")
        print(f"✅ Contains detailed glamping explanation: {'Glamorous Camping' in emergency_response}")
        print(f"✅ Contains mission: {'misión' in emergency_response.lower()}")
        print(f"✅ Contains philosophy points: {'Sostenibilidad' in emergency_response}")
        print(f"✅ Contains experience details: {'4 domos' in emergency_response}")
        print(f"✅ Contains what makes special: {'hace especiales' in emergency_response}")
        print(f"✅ Contains website: {'glampingbrillodelaluna.com' in emergency_response}")
        print(f"✅ Contains navigation: {'menú' in emergency_response.lower()}")
        
        # Verificaciones específicas
        has_detailed_explanation = 'Glamorous Camping' in emergency_response
        has_mission = 'misión' in emergency_response.lower() 
        has_philosophy_points = 'Sostenibilidad' in emergency_response
        has_experience_details = '4 domos' in emergency_response
        has_special_features = 'hace especiales' in emergency_response
        has_website = 'glampingbrillodelaluna.com' in emergency_response
        has_navigation = 'menú' in emergency_response.lower()
        
        success = all([
            len(emergency_response) > 700,
            has_detailed_explanation,
            has_mission,
            has_philosophy_points,
            has_experience_details,
            has_special_features,
            has_website,
            has_navigation
        ])
        
        print(f"   {'✅ PASS' if success else '❌ FAIL'}")
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_concepto_dual_rag_attempt():
    """Test que la función intente tanto concepto_glamping como informacion_general"""
    print("\n🧪 TEST: Dual RAG Attempt (concepto_glamping + informacion_general)")
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        validation_service = ValidationService()
        
        # Simular que solo informacion_general está disponible
        qa_chains = {"informacion_general": MockRAGChain("generic response")}
        
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # La función debería intentar informacion_general y luego usar fallback
        response = menu_service.handle_concepto_info()
        
        print(f"✅ Response generated: {len(response) > 100}")
        print(f"✅ Contains detailed info: {'filosofía' in response.lower()}")
        print(f"✅ Falls back when RAG generic: {len(response) > 800}")  # Debería ser fallback robusto
        
        success = len(response) > 800 and 'filosofía' in response.lower()
        
        print(f"   {'✅ PASS' if success else '❌ FAIL'}")
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

class MockRAGChain:
    """Mock RAG chain que devuelve respuestas genéricas para testing"""
    def __init__(self, response):
        self.response = response
    
    def run(self, query):
        return self.response

def main():
    """Ejecutar todos los tests de concepto mejorado"""
    print("🔥 TESTS DE CONCEPTO ENHANCED")
    print("=" * 50)
    
    tests = [
        ("Enhanced Concepto Fallback", test_concepto_enhanced_fallback),
        ("Concepto Fallback Consistency", test_concepto_fallback_consistency),
        ("Concepto Emergency Response", test_concepto_emergency_response),
        ("Dual RAG Attempt", test_concepto_dual_rag_attempt)
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
    print(f"\n{'='*50}")
    print("📊 RESUMEN DE TESTS CONCEPTO")
    print(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("✅ CONCEPTO ENHANCED IMPLEMENTADO CORRECTAMENTE")
        print("🚀 FUNCIÓN handle_concepto_info() LISTA PARA PRODUCCIÓN")
        return True
    else:
        print("❌ ALGUNAS MEJORAS EN CONCEPTO NECESITAN CORRECCIÓN")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)