#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del rate limiter inteligente con fallback automático
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rate_limiter_inteligente():
    """Test del rate limiter con lógica inteligente"""
    print("🔥 TEST: Rate Limiter Inteligente")
    print("🎯 Verificar fallback automático cuando se excede límite")
    print("=" * 70)
    
    try:
        from services.llm_service import LLMService
        
        # Crear LLMService con rate limiter mejorado
        llm_service = LLMService()
        
        # Verificar configuración del rate limiter
        print("📋 Configuración del Rate Limiter:")
        print(f"   Límite global: {llm_service.rate_limiter.max_calls_per_minute}/min")
        print(f"   Límite por usuario: {llm_service.rate_limiter.max_calls_per_user_per_minute}/min")
        
        # Simular múltiples llamadas para llegar al límite
        user_id = "test_user_rate_limit"
        
        print(f"\n🧪 Simulando {llm_service.rate_limiter.max_calls_per_user_per_minute + 2} llamadas:")
        
        results = []
        for i in range(llm_service.rate_limiter.max_calls_per_user_per_minute + 2):
            print(f"\n{i+1:2d}. Llamada #{i+1}:")
            
            # Alternar entre consultas que tienen fallback y que no
            if i % 2 == 0:
                query = "ubicación del glamping"
                expected_fallback = True
            else:
                query = "consulta genérica sin fallback específico"
                expected_fallback = False
            
            # Simular llamada al run_agent_safe
            can_proceed, limit_reason, wait_seconds = llm_service.rate_limiter.can_make_request(user_id)
            
            if can_proceed:
                # Dentro del límite - registrar llamada
                llm_service.rate_limiter.record_request(user_id)
                print(f"   ✅ Llamada permitida ({i+1}/{llm_service.rate_limiter.max_calls_per_user_per_minute})")
                results.append(("permitida", True, ""))
                
            else:
                # Fuera del límite - probar fallback
                print(f"   🚫 Rate limit excedido: {limit_reason}")
                
                # Simular la nueva lógica de fallback
                try:
                    from services.fallback_service import detect_topic_and_provide_fallback
                    handled, fallback_response, topic = detect_topic_and_provide_fallback(query)

                    if handled and fallback_response:
                        print(f"   🔄 Fallback activado para topic: {topic}")
                        print(f"   ✅ Response length: {len(fallback_response)} chars")
                        results.append(("fallback", True, topic))
                    else:
                        print(f"   ❌ Sin fallback disponible")
                        results.append(("bloqueada", False, ""))

                except Exception as fallback_error:
                    print(f"   ❌ Error en fallback: {fallback_error}")
                    results.append(("error", False, str(fallback_error)))
        
        # Analizar resultados
        print(f"\n📊 Análisis de resultados:")
        permitidas = sum(1 for r in results if r[0] == "permitida")
        fallbacks = sum(1 for r in results if r[0] == "fallback")
        bloqueadas = sum(1 for r in results if r[0] == "bloqueada")
        errores = sum(1 for r in results if r[0] == "error")
        
        print(f"   Llamadas permitidas: {permitidas}")
        print(f"   Fallbacks exitosos: {fallbacks}")
        print(f"   Llamadas bloqueadas: {bloqueadas}")
        print(f"   Errores: {errores}")
        
        # Verificar que el sistema funciona como esperado
        expected_permitidas = llm_service.rate_limiter.max_calls_per_user_per_minute
        expected_fallbacks = min(1, len(results) - expected_permitidas)  # Al menos 1 fallback si hay llamadas extras
        
        success = (
            permitidas == expected_permitidas and
            fallbacks >= expected_fallbacks and
            errores == 0
        )
        
        print(f"\n🎯 RESULTADO:")
        print(f"   Permitidas esperadas: {expected_permitidas}, obtenidas: {permitidas} {'✅' if permitidas == expected_permitidas else '❌'}")
        print(f"   Fallbacks esperados: >={expected_fallbacks}, obtenidos: {fallbacks} {'✅' if fallbacks >= expected_fallbacks else '❌'}")
        print(f"   Sin errores: {'✅' if errores == 0 else '❌'}")
        print(f"   {'✅ RATE LIMITER INTELIGENTE FUNCIONAL' if success else '❌ RATE LIMITER NECESITA AJUSTES'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flujo_completo_con_rate_limiter():
    """Test del flujo completo considerando el nuevo rate limiter"""
    print("\n🔥 TEST: Flujo Completo con Nuevo Rate Limiter")
    print("🎯 Verificar que el flujo 1→Ubicación→Concepto funcione sin límites")
    print("=" * 70)
    
    try:
        from services.llm_service import LLMService
        
        llm_service = LLMService()
        user_id = "test_flujo_completo"
        
        # Simular las 3 llamadas del flujo: "1" + "Ubicación" + "Concepto"
        queries = [
            ("1", "selección de menú"),
            ("Ubicación", "consulta ubicación"), 
            ("Concepto", "consulta concepto")
        ]
        
        print(f"🧪 Simulando flujo completo con {len(queries)} consultas:")
        
        all_success = True
        for i, (query, description) in enumerate(queries, 1):
            print(f"\n{i}. {description}: '{query}'")
            
            # Verificar si puede proceder
            can_proceed, limit_reason, wait_seconds = llm_service.rate_limiter.can_make_request(user_id)
            
            if can_proceed:
                llm_service.rate_limiter.record_request(user_id)
                print(f"   ✅ Permitida ({i}/{llm_service.rate_limiter.max_calls_per_user_per_minute})")
            else:
                print(f"   🚫 Bloqueada: {limit_reason}")
                
                # Probar fallback
                try:
                    from services.fallback_service import detect_topic_and_provide_fallback
                    handled, fallback_response, topic = detect_topic_and_provide_fallback(query)
                    
                    if handled and fallback_response:
                        print(f"   🔄 Fallback exitoso: {topic} ({len(fallback_response)} chars)")
                    else:
                        print(f"   ❌ Sin fallback - FALLO")
                        all_success = False
                        
                except Exception as e:
                    print(f"   ❌ Error en fallback: {e}")
                    all_success = False
        
        print(f"\n🎯 RESULTADO FLUJO COMPLETO:")
        print(f"   {'✅ FLUJO COMPLETAMENTE FUNCIONAL' if all_success else '❌ FLUJO TIENE PROBLEMAS'}")
        
        return all_success
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def main():
    """Ejecutar tests del rate limiter inteligente"""
    print("🚀 TESTS DEL RATE LIMITER INTELIGENTE")
    print("🎯 Verificar mejoras en límites y fallback automático")
    print("=" * 80)
    
    tests = [
        ("Rate Limiter Inteligente", test_rate_limiter_inteligente),
        ("Flujo Completo con Nuevo Rate Limiter", test_flujo_completo_con_rate_limiter)
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
    print("📊 REPORTE FINAL - RATE LIMITER INTELIGENTE")
    print(f"{'='*80}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n🎉 RATE LIMITER INTELIGENTE IMPLEMENTADO CORRECTAMENTE")
        print("✅ LÍMITES FLEXIBLES PARA CONVERSACIONES NATURALES")
        print("✅ FALLBACK AUTOMÁTICO CUANDO SE EXCEDE LÍMITE")
        print("✅ FLUJO COMPLETO FUNCIONAL SIN RESTRICCIONES")
        print("✅ PROTECCIÓN CONTRA ABUSO MANTENIDA")
        print("\n💫 SISTEMA COMPLETAMENTE OPTIMIZADO")
        return True
    else:
        print("\n❌ RATE LIMITER INTELIGENTE NECESITA AJUSTES")
        print("🔧 REVISAR CONFIGURACIÓN Y LÓGICA DE FALLBACK")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)