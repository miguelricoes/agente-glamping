#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de verificación final del flujo corregido completo
Simula exactamente el problema original y verifica que esté resuelto
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flujo_original_problema():
    """Test del flujo exacto que tenía el problema original"""
    print("🔥 TEST: Flujo Original del Problema - ERROR 429 OpenAI")
    print("=" * 65)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        # Simular el problema original - sin RAG chains (OpenAI fallando)
        validation_service = ValidationService()
        qa_chains = {}  # Sin RAG → simula OpenAI fallando
        
        menu_service = create_menu_service(qa_chains, validation_service)
        user_state = {"current_flow": "none"}
        
        print("\n🧪 PASO 1: Usuario escribe '1' (debe mostrar submenú información)")
        response_1 = menu_service.handle_menu_selection("1", user_state)
        
        success_1 = (
            len(response_1) > 100 and 
            "INFORMACIÓN" in response_1 and 
            "UBICACIÓN" in response_1 and
            "CONCEPTO" in response_1
        )
        
        print(f"   {'✅ PASS' if success_1 else '❌ FAIL'} - Submenú mostrado correctamente")
        print(f"   📏 Response length: {len(response_1)} chars")
        
        print("\n🧪 PASO 2: Usuario escribe 'Ubicación' (OpenAI falla - debe usar fallback)")
        response_2 = menu_service.handle_ubicacion_info()
        
        # Verificar que el fallback sea robusto
        success_2 = (
            len(response_2) > 500 and  # Respuesta robusta
            "GPS" in response_2 and  # Contiene coordenadas
            "Guatavita" in response_2 and  # Ubicación específica
            "305 461 4926" in response_2 and  # WhatsApp
            "menú" in response_2.lower()  # Navegación
        )
        
        print(f"   {'✅ PASS' if success_2 else '❌ FAIL'} - Información ubicación completa")
        print(f"   📏 Response length: {len(response_2)} chars")
        print(f"   🗺️ Contains GPS: {'✅' if 'GPS' in response_2 else '❌'}")
        print(f"   📍 Contains Guatavita: {'✅' if 'Guatavita' in response_2 else '❌'}")
        print(f"   📞 Contains WhatsApp: {'✅' if '305 461 4926' in response_2 else '❌'}")
        
        print("\n🧪 PASO 3: Usuario escribe 'Concepto' (OpenAI falla - debe usar fallback)")
        response_3 = menu_service.handle_concepto_info()
        
        # Verificar que el fallback sea robusto
        success_3 = (
            len(response_3) > 800 and  # Respuesta muy robusta
            "glamping" in response_3.lower() and  # Concepto presente
            "filosofía" in response_3.lower() and  # Filosofía explicada
            "Guatavita" in response_3 and  # Ubicación específica
            "glampingbrillodelaluna.com" in response_3 and  # Website
            "menú" in response_3.lower()  # Navegación
        )
        
        print(f"   {'✅ PASS' if success_3 else '❌ FAIL'} - Información concepto completa")
        print(f"   📏 Response length: {len(response_3)} chars")
        print(f"   🏕️ Contains glamping: {'✅' if 'glamping' in response_3.lower() else '❌'}")
        print(f"   💭 Contains filosofía: {'✅' if 'filosofía' in response_3.lower() else '❌'}")
        print(f"   🌐 Contains website: {'✅' if 'glampingbrillodelaluna.com' in response_3 else '❌'}")
        
        overall_success = success_1 and success_2 and success_3
        
        print(f"\n🎯 RESULTADO FINAL DEL FLUJO:")
        print(f"   Paso 1 (Menú): {'✅' if success_1 else '❌'}")
        print(f"   Paso 2 (Ubicación): {'✅' if success_2 else '❌'}")
        print(f"   Paso 3 (Concepto): {'✅' if success_3 else '❌'}")
        print(f"\n   {'🎉 PROBLEMA RESUELTO COMPLETAMENTE' if overall_success else '❌ PROBLEMA PERSISTE'}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Error en test de flujo: {e}")
        return False

def test_capas_de_fallback():
    """Test específico de las 3 capas de fallback implementadas"""
    print("\n🔥 TEST: Triple Capa de Fallback")
    print("=" * 50)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        from services.fallback_service import detect_topic_and_provide_fallback
        
        validation_service = ValidationService()
        
        print("\n📋 CAPA 1: RAG Chain (simulando falla)")
        # Sin RAG chains → Capa 1 falla automáticamente
        qa_chains = {}
        menu_service = create_menu_service(qa_chains, validation_service)
        
        print("   ❌ RAG Chain no disponible (simulado)")
        
        print("\n📋 CAPA 2: Fallback Service")
        handled_ubi, response_ubi, topic_ubi = detect_topic_and_provide_fallback("ubicación dirección donde están")
        handled_con, response_con, topic_con = detect_topic_and_provide_fallback("concepto filosofía que es glamping brillo de luna")
        
        print(f"   {'✅' if handled_ubi else '❌'} Ubicación: {topic_ubi} ({len(response_ubi)} chars)")
        print(f"   {'✅' if handled_con else '❌'} Concepto: {topic_con} ({len(response_con)} chars)")
        
        print("\n📋 CAPA 3: Emergency Response")
        emergency_ubi = menu_service._get_emergency_ubicacion_response()
        emergency_con = menu_service._get_emergency_concepto_response()
        
        print(f"   ✅ Emergency Ubicación: {len(emergency_ubi)} chars")
        print(f"   ✅ Emergency Concepto: {len(emergency_con)} chars")
        
        # Verificar que las capas están integradas
        print("\n📋 INTEGRACIÓN: Test completo sin RAG")
        final_ubi = menu_service.handle_ubicacion_info()
        final_con = menu_service.handle_concepto_info()
        
        integration_success = (
            len(final_ubi) > 500 and len(final_con) > 800 and
            "GPS" in final_ubi and "filosofía" in final_con.lower()
        )
        
        print(f"   {'✅ PASS' if integration_success else '❌ FAIL'} - Integración completa")
        print(f"   📊 Ubicación final: {len(final_ubi)} chars")
        print(f"   📊 Concepto final: {len(final_con)} chars")
        
        return integration_success
        
    except Exception as e:
        print(f"❌ Error en test de capas: {e}")
        return False

def test_validacion_respuestas_genericas():
    """Test de la validación de respuestas genéricas que dispara los fallbacks"""
    print("\n🔥 TEST: Validación de Respuestas Genéricas")
    print("=" * 50)
    
    try:
        from services.menu_service import create_menu_service
        from services.validation_service import ValidationService
        
        validation_service = ValidationService()
        qa_chains = {}
        menu_service = create_menu_service(qa_chains, validation_service)
        
        # Simular respuestas problemáticas que deberían disparar fallbacks
        problematic_responses = [
            ("", "Respuesta vacía"),
            ("Error code: 429 - Quota exceeded", "Error 429 OpenAI"),
            ("insufficient_quota", "Quota insuficiente"),
            ("Lo siento, no encontré información", "Respuesta genérica"),
            ("Como asistente AI, no tengo acceso...", "Respuesta de asistente AI"),
            ("No disponible", "Respuesta muy corta")
        ]
        
        valid_responses = [
            ("Glamping Brillo de Luna", "Respuesta específica corta"),
            ("Ubicado en Guatavita, Cundinamarca", "Ubicación específica"),
            ("Domo disponible con jacuzzi", "Información específica")
        ]
        
        print("\n📋 Respuestas PROBLEMÁTICAS (deben ser detectadas como genéricas):")
        problematic_results = []
        for response, desc in problematic_responses:
            is_generic = menu_service._is_generic_response(response)
            problematic_results.append(is_generic)
            print(f"   {'✅' if is_generic else '❌'} {desc}: \"{response}\"")
        
        print("\n📋 Respuestas VÁLIDAS (NO deben ser detectadas como genéricas):")
        valid_results = []
        for response, desc in valid_responses:
            is_generic = menu_service._is_generic_response(response)
            valid_results.append(not is_generic)  # NOT generic = válida
            print(f"   {'✅' if not is_generic else '❌'} {desc}: \"{response}\"")
        
        detection_success = (
            all(problematic_results) and  # Todas las problemáticas detectadas
            all(valid_results)  # Todas las válidas NO detectadas como genéricas
        )
        
        print(f"\n📊 RESULTADO:")
        print(f"   Problemáticas detectadas: {sum(problematic_results)}/{len(problematic_results)}")
        print(f"   Válidas NO detectadas: {sum(valid_results)}/{len(valid_results)}")
        print(f"   {'✅ PASS' if detection_success else '❌ FAIL'} - Detección de respuestas genéricas")
        
        return detection_success
        
    except Exception as e:
        print(f"❌ Error en test de validación: {e}")
        return False

def main():
    """Ejecutar verificación técnica completa del fix"""
    print("🚀 VERIFICACIÓN TÉCNICA COMPLETA DEL FIX")
    print("🎯 Validando que el problema original esté completamente resuelto")
    print("=" * 80)
    
    tests = [
        ("Flujo Original del Problema", test_flujo_original_problema),
        ("Triple Capa de Fallback", test_capas_de_fallback),
        ("Validación Respuestas Genéricas", test_validacion_respuestas_genericas)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'🔥' if test_name == 'Flujo Original del Problema' else '🧪'} EJECUTANDO: {test_name}")
        print("-" * 65)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            results.append((test_name, False))
            print(f"   ❌ FAIL - Exception: {e}")
    
    # Resumen final
    print(f"\n{'='*80}")
    print("📊 REPORTE FINAL DE VERIFICACIÓN TÉCNICA")
    print(f"{'='*80}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n🎉 VERIFICACIÓN TÉCNICA EXITOSA")
        print("✅ PROBLEMA ORIGINAL COMPLETAMENTE RESUELTO")
        print("🚀 IMPLEMENTACIÓN TÉCNICA 100% CORRECTA")
        print("📈 FLUJO DE CONVERSACIÓN ROBUSTO")
        print("🛡️ SISTEMA RESILIENTE A FALLOS DE OPENAI")
        print("\n💫 EL FIX ESTÁ PERFECTAMENTE IMPLEMENTADO")
        return True
    else:
        print("\n❌ VERIFICACIÓN TÉCNICA FALLÓ")
        print("🔧 REVISAR IMPLEMENTACIÓN")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)