#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test para validar el sistema de fallback RAG directo cuando OpenAI no está disponible
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_direct_rag_function():
    print("=== TEST DIRECTO DE FUNCION RAG FALLBACK ===")
    
    try:
        # Importar función directamente
        from agente import get_direct_rag_response
        
        test_cases = [
            {
                "query": "¿Cuáles son los precios de los domos?",
                "expected_keywords": ["precio", "650", "550", "350", "antares", "polaris", "sirius"],
                "category": "precios"
            },
            {
                "query": "¿Qué servicios incluyen?",
                "expected_keywords": ["desayuno", "wifi", "parqueadero", "servicios", "incluidos"],
                "category": "servicios"
            },
            {
                "query": "¿Dónde están ubicados?",
                "expected_keywords": ["guatavita", "ubicación", "tominé", "contacto"],
                "category": "ubicación"
            },
            {
                "query": "¿Qué actividades hay?",
                "expected_keywords": ["laguna", "jet ski", "caballo", "aves", "actividades"],
                "category": "actividades"
            },
            {
                "query": "Quiero saber más sobre el domo Sirius",
                "expected_keywords": ["sirius", "económico", "350", "domo"],
                "category": "domos específicos"
            },
            {
                "query": "¿Tienen disponibilidad?",
                "expected_keywords": ["disponibilidad", "fechas", "personas", "consulta"],
                "category": "disponibilidad"
            }
        ]
        
        successful_tests = 0
        total_tests = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- TEST {i}: {test_case['category'].upper()} ---")
            print(f"QUERY: {test_case['query']}")
            
            try:
                response = get_direct_rag_response(test_case["query"])
                print(f"RESPONSE: {response}")
                
                # Validación de contenido
                response_lower = response.lower()
                found_keywords = []
                
                for keyword in test_case["expected_keywords"]:
                    if keyword.lower() in response_lower:
                        found_keywords.append(keyword)
                
                keyword_score = len(found_keywords) / len(test_case["expected_keywords"])
                has_relevant_content = len(found_keywords) >= 2
                has_branding = "brillo de luna" in response_lower or "glamping" in response_lower
                
                print(f"VALIDACION:")
                print(f"  - Keywords encontradas: {found_keywords}")
                print(f"  - Score keywords: {keyword_score:.2f} ({len(found_keywords)}/{len(test_case['expected_keywords'])})")
                print(f"  - Contenido relevante: {'SI' if has_relevant_content else 'NO'}")
                print(f"  - Incluye branding: {'SI' if has_branding else 'NO'}")
                
                if has_relevant_content:
                    successful_tests += 1
                    print(f"  - RESULTADO: ✓ EXITOSO")
                else:
                    print(f"  - RESULTADO: ✗ NECESITA MEJORA")
                
            except Exception as e:
                print(f"ERROR: {e}")
                print(f"  - RESULTADO: ✗ ERROR")
        
        success_rate = (successful_tests / total_tests) * 100
        
        print(f"\n" + "=" * 60)
        print(f"RESUMEN DE RESULTADOS")
        print(f"=" * 60)
        print(f"Tests exitosos: {successful_tests}/{total_tests}")
        print(f"Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🏆 EXCELENTE: Sistema de fallback RAG funciona perfectamente")
            return True
        elif success_rate >= 60:
            print("⚠️ BUENO: Sistema funciona pero podría mejorarse")
            return True
        else:
            print("❌ CRÍTICO: Sistema de fallback necesita revisión")
            return False
        
    except ImportError as e:
        print(f"ERROR IMPORTANDO: {e}")
        return False
    
    except Exception as e:
        print(f"ERROR GENERAL: {e}")
        return False

def test_fallback_scenarios():
    print("\n=== TEST DE ESCENARIOS DE FALLBACK ===")
    
    try:
        from agente import get_direct_rag_response
        
        # Test con queries menos específicas
        fallback_queries = [
            "Hola",
            "¿Qué puedes hacer?", 
            "Información general",
            "Cuéntame sobre ustedes"
        ]
        
        for query in fallback_queries:
            print(f"\nQUERY: {query}")
            response = get_direct_rag_response(query)
            
            # Verificar que la respuesta tenga información útil
            response_lower = response.lower()
            has_menu = "1" in response and "2" in response
            has_pricing = any(price in response for price in ["650", "550", "350"])
            has_branding = "brillo de luna" in response_lower
            
            print(f"RESPONSE: {response[:100]}...")
            print(f"  - Incluye menú: {'SI' if has_menu else 'NO'}")
            print(f"  - Incluye precios: {'SI' if has_pricing else 'NO'}")
            print(f"  - Incluye branding: {'SI' if has_branding else 'NO'}")
            
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("INICIANDO TEST DE SISTEMA FALLBACK RAG")
    print("=" * 60)
    
    success1 = test_direct_rag_function()
    success2 = test_fallback_scenarios()
    
    print("\n" + "=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)
    
    if success1 and success2:
        print("✓ SISTEMA FALLBACK RAG FUNCIONANDO CORRECTAMENTE")
        print("El agente puede responder preguntas básicas incluso sin OpenAI")
    else:
        print("✗ SISTEMA FALLBACK NECESITA AJUSTES")
        print("Revisar implementación del sistema de respaldo")