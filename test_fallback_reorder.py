#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar que políticas se evalúe antes que concepto
"""

import sys
import os

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_fallback_order():
    """Test que políticas se evalúe antes que concepto"""
    print("🔥 TEST: Orden de Evaluación en Fallback Service")
    print("🎯 Verificar que políticas se evalúe ANTES que concepto")
    print("=" * 70)
    
    try:
        from services.fallback_service import detect_topic_and_provide_fallback
        
        test_cases = [
            {
                "input": "políticas de mascotas",
                "expected_topic": "politicas",
                "description": "Políticas directa"
            },
            {
                "input": "políticas",
                "expected_topic": "politicas", 
                "description": "Solo políticas"
            },
            {
                "input": "concepto",
                "expected_topic": "concepto",
                "description": "Solo concepto"
            },
            {
                "input": "políticas brillo de luna",
                "expected_topic": "politicas",
                "description": "Políticas con brillo de luna (conflicto)"
            },
            {
                "input": "qué políticas tienen",
                "expected_topic": "politicas",
                "description": "Pregunta sobre políticas"
            },
            {
                "input": "concepto glamping",
                "expected_topic": "concepto", 
                "description": "Concepto específico"
            }
        ]
        
        print("🧪 Ejecutando casos de prueba:")
        
        results = []
        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. {case['description']}: '{case['input']}'")
            
            handled, response, topic = detect_topic_and_provide_fallback(case['input'])
            
            success = handled and topic == case['expected_topic']
            results.append(success)
            
            print(f"   Handled: {handled}")
            print(f"   Topic detected: {topic}")
            print(f"   Expected: {case['expected_topic']}")
            print(f"   Response length: {len(response)} chars")
            print(f"   {'✅ PASS' if success else '❌ FAIL'} - {case['description']}")
            
            # Verificar contenido específico
            if topic == "politicas":
                has_politicas_content = "POLÍTICAS" in response and "MASCOTAS" in response
                print(f"   Contains políticas content: {'✅' if has_politicas_content else '❌'}")
            elif topic == "concepto":
                has_concepto_content = "CONCEPTO" in response and "Glamping" in response
                print(f"   Contains concepto content: {'✅' if has_concepto_content else '❌'}")
        
        # Resultado final
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   Tests exitosos: {passed}/{total} ({success_rate:.1f}%)")
        print(f"   {'✅ ORDEN CORRECTO' if success_rate >= 85 else '❌ ORDEN NECESITA AJUSTES'}")
        
        # Test específico del caso problemático
        print(f"\n🔍 Test específico del conflicto 'políticas brillo de luna':")
        handled, response, topic = detect_topic_and_provide_fallback("políticas brillo de luna")
        
        conflict_resolved = topic == "politicas"
        print(f"   Input: 'políticas brillo de luna'")
        print(f"   Topic detected: {topic}")
        print(f"   {'✅ CONFLICTO RESUELTO' if conflict_resolved else '❌ CONFLICTO PERSISTE'}")
        
        return success_rate >= 85 and conflict_resolved
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar test de reordenamiento"""
    print("🚀 TEST REORDENAMIENTO FALLBACK SERVICE")
    print("🎯 Verificar que políticas tenga prioridad sobre concepto")
    print("=" * 80)
    
    success = test_fallback_order()
    
    if success:
        print("\n🎉 REORDENAMIENTO EXITOSO")
        print("✅ Políticas evaluadas ANTES que concepto")
        print("✅ Conflicto 'brillo de luna' resuelto")
        print("✅ Patrones más específicos implementados")
        print("✅ Sistema de fallback optimizado")
        print("\n💫 PROBLEMA DE ORDEN DE EVALUACIÓN RESUELTO")
    else:
        print("\n❌ REORDENAMIENTO NECESITA AJUSTES")
        print("🔧 REVISAR ORDEN Y PATRONES EN FALLBACK SERVICE")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)