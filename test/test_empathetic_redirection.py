#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test para validar el nuevo sistema de Redirección Conversacional Estratégica
Sistema de respuestas empáticas que conectan emocionalmente y redirigen al glamping
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import time
from datetime import datetime

# Configuración del test
BASE_URL = "http://localhost:8080"
CHAT_ENDPOINT = f"{BASE_URL}/chat"

def test_empathetic_redirection():
    """
    Test principal para validar respuestas empáticas y redirección estratégica
    """
    print("🧪 INICIANDO TESTS DE REDIRECCIÓN CONVERSACIONAL ESTRATÉGICA")
    print("=" * 70)
    
    # Casos de test: situaciones personales/emocionales que deben activar la nueva herramienta
    test_cases = [
        {
            "name": "Tristeza/Depresión",
            "message": "Estoy muy triste, he tenido días muy difíciles últimamente",
            "expected_keywords": ["comprendo", "naturaleza", "paz", "tranquilidad", "glamping", "brillo de luna"]
        },
        {
            "name": "Estrés Laboral", 
            "message": "Estoy súper estresado con el trabajo, necesito descansar",
            "expected_keywords": ["estrés", "descanso", "escape", "naturales", "domos", "relajar"]
        },
        {
            "name": "Problemas de Pareja",
            "message": "Mi relación está pasando por momentos difíciles",
            "expected_keywords": ["pareja", "reconectar", "romántico", "momentos especiales", "ambiente"]
        },
        {
            "name": "Soledad",
            "message": "Me siento muy solo últimamente, no tengo con quien hablar",
            "expected_keywords": ["soledad", "tranquilidad", "reflexionar", "espacio", "naturaleza"]
        },
        {
            "name": "Ansiedad",
            "message": "Tengo mucha ansiedad y no sé qué hacer para calmarme",
            "expected_keywords": ["ansiedad", "calma", "aire fresco", "silencio", "paz"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 TEST {i}: {test_case['name']}")
        print(f"📝 Mensaje: '{test_case['message']}'")
        print("-" * 50)
        
        # Enviar request
        test_session_id = f"test_empathy_{int(time.time())}_{i}"
        payload = {
            "input": test_case["message"],
            "session_id": test_session_id
        }
        
        try:
            response = requests.post(
                CHAT_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                agent_response = response_data.get("response", "")
                
                print(f"✅ Respuesta recibida:")
                print(f"📄 {agent_response}")
                
                # Validar que la respuesta contenga elementos empáticos y de redirección
                empathy_score = 0
                redirection_score = 0
                found_keywords = []
                
                response_lower = agent_response.lower()
                
                # Verificar keywords esperadas
                for keyword in test_case["expected_keywords"]:
                    if keyword.lower() in response_lower:
                        found_keywords.append(keyword)
                        if keyword.lower() in ["comprendo", "entiendo", "sentir", "emociones"]:
                            empathy_score += 1
                        elif keyword.lower() in ["glamping", "domos", "brillo de luna", "naturaleza"]:
                            redirection_score += 1
                
                # Verificar estructura de respuesta empática
                has_empathy = any(word in response_lower for word in [
                    "comprendo", "entiendo", "sé", "momentos difíciles", "situación"
                ])
                
                has_redirection = any(word in response_lower for word in [
                    "glamping", "domos", "naturaleza", "brillo de luna", "tranquilidad", "paz"
                ])
                
                has_invitation = any(word in response_lower for word in [
                    "te gustaría", "podrías", "considera", "opciones", "reservar"
                ])
                
                # Calcular score total
                total_score = 0
                if has_empathy:
                    total_score += 3
                if has_redirection:
                    total_score += 3
                if has_invitation:
                    total_score += 2
                if len(found_keywords) >= 2:
                    total_score += 2
                
                results.append({
                    "test": test_case['name'],
                    "message": test_case['message'],
                    "response": agent_response,
                    "empathy": has_empathy,
                    "redirection": has_redirection,
                    "invitation": has_invitation,
                    "keywords_found": found_keywords,
                    "score": total_score,
                    "max_score": 10,
                    "success": total_score >= 6
                })
                
                print(f"🎯 Score: {total_score}/10")
                print(f"❤️ Empatía: {'✅' if has_empathy else '❌'}")
                print(f"🔄 Redirección: {'✅' if has_redirection else '❌'}")
                print(f"💌 Invitación: {'✅' if has_invitation else '❌'}")
                print(f"🏷️ Keywords encontradas: {found_keywords}")
                print(f"🏆 Resultado: {'✅ EXITOSO' if total_score >= 6 else '❌ NECESITA MEJORA'}")
                
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                print(f"📄 Respuesta: {response.text}")
                results.append({
                    "test": test_case['name'],
                    "error": f"HTTP {response.status_code}",
                    "success": False
                })
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "test": test_case['name'],
                "error": str(e),
                "success": False
            })
        
        # Pausa entre tests para evitar rate limits
        time.sleep(2)
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 70)
    
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    for result in results:
        status = "✅ EXITOSO" if result.get('success', False) else "❌ FALLÓ"
        score_info = f"({result.get('score', 0)}/10)" if 'score' in result else ""
        print(f"• {result['test']}: {status} {score_info}")
    
    print(f"\n🎯 TASA DE ÉXITO: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🏆 EXCELENTE: El sistema de redirección empática funciona correctamente")
    elif success_rate >= 60:
        print("⚠️ BUENO: El sistema funciona pero puede necesitar ajustes menores")
    else:
        print("❌ CRÍTICO: El sistema necesita revisión y mejoras significativas")
    
    # Guardar resultados detallados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_empathetic_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate
            },
            "detailed_results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📄 Resultados detallados guardados en: {results_file}")
    
    return success_rate >= 60

def test_normal_glamping_questions():
    """
    Test para verificar que las preguntas normales de glamping siguen funcionando correctamente
    """
    print("\n" + "=" * 70)
    print("🧪 TEST DE REGRESIÓN - PREGUNTAS NORMALES DE GLAMPING")
    print("=" * 70)
    
    normal_questions = [
        "¿Cuáles son los precios de los domos?",
        "¿Qué servicios incluyen los domos?",
        "¿Tienen disponibilidad para diciembre?",
        "¿Dónde están ubicados?"
    ]
    
    for i, question in enumerate(normal_questions, 1):
        print(f"\n🧪 TEST REGRESIÓN {i}: {question}")
        
        test_session_id = f"test_normal_{int(time.time())}_{i}"
        payload = {
            "input": question,
            "session_id": test_session_id
        }
        
        try:
            response = requests.post(
                CHAT_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                response_data = response.json()
                agent_response = response_data.get("response", "")
                
                # Verificar que no se esté usando la herramienta empática
                if "RespuestaEmpaticaYRedirection" in str(response_data):
                    print("❌ ERROR: Se activó la herramienta empática en pregunta normal")
                else:
                    print("✅ Pregunta normal procesada correctamente")
                    
                print(f"📄 Respuesta: {agent_response[:100]}...")
                
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    print("INICIANDO TESTS DEL SISTEMA DE REDIRECCION EMPATICA")
    print("Asegurate de que el servidor este ejecutandose en http://localhost:8080")
    print()
    
    # Test principal
    success = test_empathetic_redirection()
    
    # Test de regresión
    test_normal_glamping_questions()
    
    print("\nTESTS COMPLETADOS")
    
    if success:
        print("El sistema de Redireccion Conversacional Estrategica esta funcionando correctamente!")
    else:
        print("El sistema necesita ajustes. Revisa los resultados detallados.")