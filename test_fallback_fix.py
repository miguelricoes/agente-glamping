#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar que el fix de fallback funciona correctamente
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ubicacion_fallback():
    """Test del fallback para ubicación"""
    print("🧪 TEST: Fallback de Ubicación")
    
    try:
        from services.fallback_service import detect_topic_and_provide_fallback
        
        # Test 1: Fallback service directamente
        handled, response, topic = detect_topic_and_provide_fallback("ubicación")
        
        print(f"✅ Handled: {handled}")
        print(f"✅ Topic: {topic}")
        print(f"✅ Response length: {len(response)} chars")
        print(f"✅ Contains GPS: {'GPS' in response}")
        print(f"✅ Contains WhatsApp: {'305 461 4926' in response}")
        
        return handled and len(response) > 100
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_concepto_fallback():
    """Test del fallback para concepto"""
    print("\n🧪 TEST: Fallback de Concepto")
    
    try:
        from services.fallback_service import detect_topic_and_provide_fallback
        
        # Test 2: Fallback service para concepto
        handled, response, topic = detect_topic_and_provide_fallback("concepto glamping")
        
        print(f"✅ Handled: {handled}")
        print(f"✅ Topic: {topic}")
        print(f"✅ Response length: {len(response)} chars")
        print(f"✅ Contains filosofía: {'filosofía' in response.lower()}")
        print(f"✅ Contains glamping: {'glamping' in response.lower()}")
        
        return handled and len(response) > 100
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_menu_service_integration():
    """Test de integración con menu service"""
    print("\n🧪 TEST: Menu Service Integration")
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        # Crear servicios mock
        validation_service = ValidationService()
        qa_chains = {}  # Simular que no hay RAG chains
        
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Test ubicación sin RAG
        ubicacion_response = menu_service.handle_ubicacion_info()
        
        print(f"✅ Menu ubicacion response length: {len(ubicacion_response)} chars")
        print(f"✅ Contains GPS coordinates: {'GPS' in ubicacion_response or 'Coordenadas' in ubicacion_response}")
        print(f"✅ Contains WhatsApp: {'305 461 4926' in ubicacion_response}")
        print(f"✅ Has navigation options: {'menú' in ubicacion_response.lower()}")
        
        # Test concepto sin RAG
        concepto_response = menu_service.handle_concepto_info()
        
        print(f"✅ Menu concepto response length: {len(concepto_response)} chars")
        print(f"✅ Contains glamping concept: {'glamping' in concepto_response.lower()}")
        print(f"✅ Has navigation options: {'menú' in concepto_response.lower()}")
        
        return len(ubicacion_response) > 200 and len(concepto_response) > 200
        
    except Exception as e:
        print(f"❌ Error en menu integration: {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("🔥 TESTS DE FALLBACK CONSISTENCY FIX")
    print("=" * 50)
    
    tests = [
        ("Ubicación Fallback", test_ubicacion_fallback),
        ("Concepto Fallback", test_concepto_fallback),
        ("Menu Integration", test_menu_service_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🚀 Ejecutando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"   ❌ FAIL - Exception: {e}")
    
    # Resumen final
    print(f"\n{'='*50}")
    print("📊 RESUMEN DE TESTS")
    print(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("✅ TODOS LOS TESTS PASARON - FIX IMPLEMENTADO CORRECTAMENTE")
        return True
    else:
        print("❌ ALGUNOS TESTS FALLARON - REVISAR IMPLEMENTACIÓN")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)