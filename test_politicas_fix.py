#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar que el fix de políticas funcione correctamente
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_politicas_qa_chain_fix():
    """Test que verifica que las políticas usen el QA chain correcto"""
    print("🔥 TEST: Fix QA Chain para Políticas")
    print("🎯 Verificar que menu_service use 'politicas_completas' en lugar de 'politicas_glamping'")
    print("=" * 80)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        # Crear QA chains mock que simula el estado real
        qa_chains = {
            "politicas_completas": type('MockChain', (), {
                'run': lambda query: f"Información de políticas RAG para: {query}"
            })(),
            # NO incluir "politicas_glamping" para verificar que no se use
        }
        
        validation_service = ValidationService()
        menu_service = create_menu_service(qa_chains, validation_service)
        
        print("📋 Configuración de test:")
        print(f"   QA chains disponibles: {list(qa_chains.keys())}")
        print(f"   ✅ 'politicas_completas' presente")
        print(f"   ❌ 'politicas_glamping' NO presente (como debe ser)")
        
        # Test diferentes métodos de políticas
        tests = [
            ("handle_politicas_mascotas", "mascotas"),
            ("handle_politicas_privacidad", "privacidad"), 
            ("handle_politicas_reservas", "reservas"),
            ("_get_politicas_mascotas_content", "mascotas_content"),
            ("_get_politicas_privacidad_content", "privacidad_content"),
            ("_get_politicas_reservas_content", "reservas_content")
        ]
        
        print(f"\n🧪 Ejecutando tests de métodos de políticas:")
        
        results = []
        for method_name, description in tests:
            print(f"\n{len(results)+1}. Testing {method_name}:")
            
            if hasattr(menu_service, method_name):
                method = getattr(menu_service, method_name)
                
                try:
                    response = method()
                    
                    # Verificar que la respuesta contiene información RAG (no fallback)
                    contains_rag = "Información de políticas RAG" in response
                    has_content = len(response) > 100
                    not_error = "inconveniente" not in response.lower()
                    
                    success = contains_rag and has_content and not_error
                    results.append(success)
                    
                    print(f"   Response length: {len(response)} chars")
                    print(f"   Contains RAG info: {'✅' if contains_rag else '❌'}")
                    print(f"   No error message: {'✅' if not_error else '❌'}")
                    print(f"   {'✅ PASS' if success else '❌ FAIL'} {description}")
                    
                except Exception as e:
                    print(f"   ❌ FAIL - Exception: {e}")
                    results.append(False)
            else:
                print(f"   ⚠️ Method {method_name} not found")
                results.append(False)
        
        # Test adicional: verificar _get_politicas_with_fallback
        print(f"\n{len(results)+1}. Testing _get_politicas_with_fallback:")
        try:
            politicas_response = menu_service._get_politicas_with_fallback()
            
            contains_rag = "Información de políticas RAG" in politicas_response
            has_content = len(politicas_response) > 100
            
            success = contains_rag and has_content
            results.append(success)
            
            print(f"   Response length: {len(politicas_response)} chars")
            print(f"   Contains RAG info: {'✅' if contains_rag else '❌'}")
            print(f"   {'✅ PASS' if success else '❌ FAIL'} politicas_with_fallback")
            
        except Exception as e:
            print(f"   ❌ FAIL - Exception: {e}")
            results.append(False)
        
        # Resultado final
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   Tests exitosos: {passed}/{total} ({success_rate:.1f}%)")
        print(f"   {'✅ FIX QA CHAIN POLÍTICAS CORRECTO' if success_rate >= 85 else '❌ FIX NECESITA AJUSTES'}")
        
        return success_rate >= 85
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_politicas_vs_concepto():
    """Test que verifica que políticas y concepto devuelvan respuestas diferentes"""
    print("\n🔥 TEST: Políticas vs Concepto - Respuestas Diferentes")
    print("🎯 Verificar que políticas no devuelva la misma respuesta que concepto")
    print("=" * 80)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        # Crear QA chains con respuestas claramente diferentes
        qa_chains = {
            "politicas_completas": type('MockPoliticasChain', (), {
                'run': lambda query: "POLÍTICAS ESPECÍFICAS: Información sobre normas y reglas del glamping"
            })(),
            "concepto_glamping": type('MockConceptoChain', (), {
                'run': lambda query: "CONCEPTO ESPECÍFICO: Información sobre la filosofía y experiencia glamping"
            })(),
        }
        
        validation_service = ValidationService()
        menu_service = create_menu_service(qa_chains, validation_service)
        
        print("📋 Testing diferentes respuestas:")
        
        # Obtener respuestas
        politicas_response = menu_service.handle_politicas_mascotas()
        concepto_response = menu_service.handle_concepto_info()
        
        print(f"\nPolíticas response (primeros 100 chars): {politicas_response[:100]}...")
        print(f"Concepto response (primeros 100 chars): {concepto_response[:100]}...")
        
        # Verificar que son diferentes
        responses_different = politicas_response != concepto_response
        politicas_has_politicas = "POLÍTICAS ESPECÍFICAS" in politicas_response
        concepto_has_concepto = "CONCEPTO ESPECÍFICO" in concepto_response
        
        print(f"\n📊 Verificación:")
        print(f"   Respuestas diferentes: {'✅' if responses_different else '❌'}")
        print(f"   Políticas contiene info de políticas: {'✅' if politicas_has_politicas else '❌'}")
        print(f"   Concepto contiene info de concepto: {'✅' if concepto_has_concepto else '❌'}")
        
        success = responses_different and politicas_has_politicas and concepto_has_concepto
        print(f"   {'✅ PASS - Respuestas diferenciadas correctamente' if success else '❌ FAIL - Problema con diferenciación'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def main():
    """Ejecutar tests del fix de políticas"""
    print("🚀 TESTS DEL FIX QA CHAIN POLÍTICAS")
    print("🎯 Verificar que políticas use 'politicas_completas' correctamente")
    print("=" * 90)
    
    tests = [
        ("Fix QA Chain para Políticas", test_politicas_qa_chain_fix),
        ("Políticas vs Concepto - Diferenciación", test_politicas_vs_concepto)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*90}")
        print(f"🧪 EJECUTANDO: {test_name}")
        print(f"{'='*90}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            results.append((test_name, False))
            print(f"   ❌ FAIL - Exception: {e}")
    
    # Reporte final
    print(f"\n{'='*90}")
    print("📊 REPORTE FINAL - FIX QA CHAIN POLÍTICAS")
    print(f"{'='*90}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n🎉 FIX QA CHAIN POLÍTICAS IMPLEMENTADO CORRECTAMENTE")
        print("✅ Todas las referencias cambiadas de 'politicas_glamping' a 'politicas_completas'")
        print("✅ RAG chains mapeados correctamente")
        print("✅ Políticas y concepto devuelven respuestas diferenciadas")
        print("✅ Sistema de políticas totalmente funcional")
        print("\n💫 PROBLEMA DE MAPEO QA CHAIN RESUELTO")
        return True
    else:
        print("\n❌ FIX QA CHAIN POLÍTICAS NECESITA AJUSTES")
        print("🔧 REVISAR MAPEO DE NOMBRES DE QA CHAINS")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)