#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de Resiliencia del Agente REAL - Glamping Brillo de Luna
Pruebas con la implementación real del agente para validar comportamiento
"""

import os
import sys
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Cargar variables de entorno
load_dotenv('.env.local')
load_dotenv()

# Importar el agente standalone real
try:
    from agente_standalone import process_whatsapp_message_standalone
    from services.conversation_service import process_chat_conversation
    from services.llm_service import get_llm_service
    from services.validation_service import ValidationService
    from services.memory_service import create_memory_directory
    from utils.logger import get_logger
    REAL_AGENT_AVAILABLE = True
    print("✅ Agente real importado correctamente")
except Exception as e:
    print(f"❌ No se pudo importar el agente real: {e}")
    REAL_AGENT_AVAILABLE = False

class RealAgentResilienceTest:
    """Test de resiliencia con el agente real implementado"""
    
    def __init__(self):
        self.test_user_id = "test_resilience_user_" + str(uuid.uuid4())[:8]
        self.conversation_history = []
        self.test_results = {
            "connection_test": False,
            "flow_detection": [],
            "memory_coherence": [],
            "strategic_redirect": [],
            "conversation_flow": [],
            "overall_score": 0
        }
        
        print("🔥 PRUEBA DE RESILIENCIA CON AGENTE REAL")
        print("🎯 Glamping Brillo de Luna - Implementación Completa")
        print("=" * 70)
        
        # Configurar logger para tests
        self.logger = get_logger(__name__)
    
    def test_agent_connection(self):
        """Probar conexión básica con el agente"""
        print("🔌 Probando conexión con el agente real...")
        
        if not REAL_AGENT_AVAILABLE:
            print("❌ Agente real no disponible - usando modo simulado")
            self.test_results["connection_test"] = False
            return False
        
        try:
            # Test básico de conexión
            test_response = self.send_message_to_agent("Hola")
            
            if test_response and len(test_response) > 10:
                print("✅ Conexión con agente real establecida")
                print(f"   Respuesta de prueba: {test_response[:100]}...")
                self.test_results["connection_test"] = True
                return True
            else:
                print("❌ Respuesta del agente inválida")
                self.test_results["connection_test"] = False
                return False
                
        except Exception as e:
            print(f"❌ Error conectando con agente: {e}")
            self.test_results["connection_test"] = False
            return False
    
    def send_message_to_agent(self, message):
        """Enviar mensaje al agente real y obtener respuesta"""
        try:
            if REAL_AGENT_AVAILABLE:
                # Usar el proceso principal del agente
                response_data = process_whatsapp_message_standalone(message, self.test_user_id)
                
                if isinstance(response_data, dict):
                    response = response_data.get("response", "")
                elif isinstance(response_data, str):
                    response = response_data
                else:
                    response = str(response_data)
                
                # Guardar en historial
                self.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "input": message,
                    "output": response,
                    "user_id": self.test_user_id
                })
                
                return response
            else:
                return "Agente no disponible en modo de prueba"
                
        except Exception as e:
            self.logger.error(f"Error enviando mensaje al agente: {e}")
            return f"Error: {str(e)}"
    
    def test_real_flow_detection(self):
        """Probar detección de flujos con el agente real"""
        print("\n🔍 PRUEBA REAL: DETECCIÓN DE FLUJOS")
        print("-" * 50)
        
        test_cases = [
            ("1", "Menú opción 1"),
            ("Información sobre domos", "Consulta por domos"),
            ("Quiero hacer una reserva", "Solicitud de reserva"),
            ("2", "Menú opción 2"),
            ("Cuáles son las políticas", "Consulta políticas"),
            ("disponibilidad", "Consulta disponibilidad")
        ]
        
        successful_detections = 0
        
        for message, description in test_cases:
            print(f"\n📝 Test: {description}")
            print(f"   Input: '{message}'")
            
            response = self.send_message_to_agent(message)
            
            # Analizar la respuesta para detectar si el flujo fue identificado correctamente
            response_lower = response.lower()
            
            flow_detected = False
            detected_flow = "unknown"
            
            # Detección heurística de flujos
            if any(word in response_lower for word in ['domo', 'antares', 'polaris', 'sirius', 'centaury']):
                flow_detected = True
                detected_flow = "domos"
            elif any(word in response_lower for word in ['política', 'cancelación', 'check-in', 'servicio']):
                flow_detected = True
                detected_flow = "policies"
            elif any(word in response_lower for word in ['reserva', 'fecha', 'persona', 'disponibilidad']):
                flow_detected = True
                detected_flow = "reservation"
            elif any(word in response_lower for word in ['ubicación', 'contacto', 'whatsapp', 'teléfono']):
                flow_detected = True
                detected_flow = "contact"
            
            if flow_detected:
                successful_detections += 1
                status = "✅ DETECTADO"
            else:
                status = "❌ NO DETECTADO"
            
            self.test_results["flow_detection"].append({
                "test": description,
                "input": message,
                "detected_flow": detected_flow,
                "success": flow_detected,
                "response": response[:200] + "..." if len(response) > 200 else response
            })
            
            print(f"   Flow detectado: {detected_flow}")
            print(f"   Status: {status}")
            print(f"   Respuesta: {response[:100]}...")
        
        detection_rate = (successful_detections / len(test_cases)) * 100
        print(f"\n📊 Tasa de detección de flujos: {detection_rate:.1f}%")
        
        return detection_rate >= 70
    
    def test_real_memory_coherence(self):
        """Probar coherencia de memoria conversacional real"""
        print("\n🧠 PRUEBA REAL: MEMORIA CONVERSACIONAL")
        print("-" * 50)
        
        print("\n📝 Secuencia conversacional para probar memoria:")
        
        # Conversación secuencial
        messages = [
            "¿Qué domos tienen disponibles?",
            "Cuéntame más sobre el Domo Polaris",
            "¿Cuál es el precio de ese domo?",
            "¿Y cuántas personas caben?"
        ]
        
        responses = []
        context_maintained = True
        
        for i, message in enumerate(messages, 1):
            print(f"\n{i}️⃣ {message}")
            response = self.send_message_to_agent(message)
            responses.append(response)
            print(f"   Respuesta: {response[:150]}...")
            
            # Verificar contexto en las respuestas posteriores
            if i >= 3:  # A partir de la tercera pregunta, debe mantener contexto
                if i == 3 and "polaris" not in response.lower():
                    context_maintained = False
                    print("   ⚠️ Posible pérdida de contexto")
                elif i == 4 and not any(word in response.lower() for word in ["polaris", "4", "cuatro", "personas"]):
                    context_maintained = False
                    print("   ⚠️ Contexto no mantenido")
        
        self.test_results["memory_coherence"].append({
            "test": "Secuencia conversacional completa",
            "messages_count": len(messages),
            "context_maintained": context_maintained,
            "success": context_maintained
        })
        
        status = "✅ MANTENIDO" if context_maintained else "❌ PERDIDO"
        print(f"\n📊 Contexto conversacional: {status}")
        
        return context_maintained
    
    def test_real_strategic_redirect(self):
        """Probar redirección estratégica con agente real"""
        print("\n🎯 PRUEBA REAL: REDIRECCIÓN ESTRATÉGICA")
        print("-" * 50)
        
        out_of_domain_cases = [
            "¿Cómo está el clima hoy?",
            "¿Dónde puedo adoptar un perro?", 
            "¿Qué opinas de la política actual?",
            "¿Cómo cocinar pasta?",
            "Estoy muy estresado del trabajo",
            "Necesito unas vacaciones relajantes"
        ]
        
        successful_redirects = 0
        
        for message in out_of_domain_cases:
            print(f"\n📝 Test fuera de dominio: '{message}'")
            response = self.send_message_to_agent(message)
            
            response_lower = response.lower()
            
            # Verificar que NO sea un menú estático simple
            is_menu_response = ("1️⃣" in response and "2️⃣" in response and "3️⃣" in response and len(response) < 300)
            
            # Verificar que mencione el glamping o redirija adecuadamente
            mentions_glamping = any(word in response_lower for word in 
                                  ['glamping', 'brillo', 'luna', 'naturaleza', 'descansar', 'relajar', 'domo'])
            
            # Verificar que sea una respuesta empática/contextual
            is_contextual = any(word in response_lower for word in 
                              ['entiendo', 'comprendo', 'ayudarte', 'especializo', 'aquí'])
            
            redirect_success = (not is_menu_response and 
                              mentions_glamping and 
                              is_contextual)
            
            if redirect_success:
                successful_redirects += 1
                status = "✅ REDIRIGIDO"
            else:
                status = "❌ NO REDIRIGIDO"
            
            self.test_results["strategic_redirect"].append({
                "test": message,
                "is_menu_response": is_menu_response,
                "mentions_glamping": mentions_glamping,
                "is_contextual": is_contextual,
                "success": redirect_success,
                "response": response[:200] + "..." if len(response) > 200 else response
            })
            
            print(f"   Evita menú: {'✅' if not is_menu_response else '❌'}")
            print(f"   Menciona glamping: {'✅' if mentions_glamping else '❌'}")
            print(f"   Es contextual: {'✅' if is_contextual else '❌'}")
            print(f"   Status: {status}")
        
        redirect_rate = (successful_redirects / len(out_of_domain_cases)) * 100
        print(f"\n📊 Tasa de redirección exitosa: {redirect_rate:.1f}%")
        
        return redirect_rate >= 70
    
    def test_conversation_flow(self):
        """Probar flujo conversacional completo"""
        print("\n💬 PRUEBA REAL: FLUJO CONVERSACIONAL COMPLETO")
        print("-" * 50)
        
        # Simular conversación real de usuario interesado
        conversation = [
            "Hola",
            "¿Qué es Glamping Brillo de Luna?",
            "¿Qué domos tienen?",
            "Me interesa el Domo Polaris",
            "¿Cuál es el precio?",
            "¿Está disponible para el próximo fin de semana?",
            "Quiero hacer una reserva",
            "Muchas gracias por la información"
        ]
        
        successful_interactions = 0
        
        print("\n📝 Simulando conversación real:")
        
        for i, message in enumerate(conversation, 1):
            print(f"\n{i}️⃣ Usuario: {message}")
            response = self.send_message_to_agent(message)
            print(f"   Agente: {response[:200]}..." if len(response) > 200 else f"   Agente: {response}")
            
            # Evaluar calidad de respuesta
            response_lower = response.lower()
            
            interaction_success = False
            
            if i == 1:  # Saludo
                interaction_success = any(word in response_lower for word in ['hola', 'bienvenido', 'ayudarte'])
            elif i == 2:  # Explicación del glamping
                interaction_success = any(word in response_lower for word in ['glamping', 'naturaleza', 'experiencia'])
            elif i == 3:  # Lista de domos
                interaction_success = any(word in response_lower for word in ['antares', 'polaris', 'sirius', 'centaury'])
            elif i == 4:  # Información específica
                interaction_success = 'polaris' in response_lower
            elif i == 5:  # Precio
                interaction_success = any(word in response_lower for word in ['precio', '$', 'costo', 'tarifa'])
            elif i == 6:  # Disponibilidad
                interaction_success = any(word in response_lower for word in ['disponibilidad', 'fecha', 'consultar'])
            elif i == 7:  # Proceso de reserva
                interaction_success = any(word in response_lower for word in ['reserva', 'datos', 'información'])
            elif i == 8:  # Agradecimiento
                interaction_success = any(word in response_lower for word in ['gracias', 'servicio', 'contacto'])
            
            if interaction_success:
                successful_interactions += 1
            
            self.test_results["conversation_flow"].append({
                "step": i,
                "user_message": message,
                "agent_response": response,
                "success": interaction_success
            })
        
        conversation_success_rate = (successful_interactions / len(conversation)) * 100
        print(f"\n📊 Éxito en flujo conversacional: {conversation_success_rate:.1f}%")
        
        return conversation_success_rate >= 75
    
    def calculate_real_overall_score(self):
        """Calcular puntuación final basada en pruebas reales"""
        if not self.test_results["connection_test"]:
            return 0  # Si no hay conexión, score es 0
        
        scores = []
        
        # Detección de flujos (25%)
        flow_success = sum(1 for r in self.test_results["flow_detection"] if r["success"])
        flow_total = len(self.test_results["flow_detection"])
        if flow_total > 0:
            scores.append((flow_success / flow_total) * 0.25)
        
        # Coherencia de memoria (20%)
        memory_success = sum(1 for r in self.test_results["memory_coherence"] if r["success"])
        memory_total = len(self.test_results["memory_coherence"])
        if memory_total > 0:
            scores.append((memory_success / memory_total) * 0.20)
        
        # Redirección estratégica (25%)
        redirect_success = sum(1 for r in self.test_results["strategic_redirect"] if r["success"])
        redirect_total = len(self.test_results["strategic_redirect"])
        if redirect_total > 0:
            scores.append((redirect_success / redirect_total) * 0.25)
        
        # Flujo conversacional (30%)
        conversation_success = sum(1 for r in self.test_results["conversation_flow"] if r["success"])
        conversation_total = len(self.test_results["conversation_flow"])
        if conversation_total > 0:
            scores.append((conversation_success / conversation_total) * 0.30)
        
        overall_score = sum(scores) * 100
        self.test_results["overall_score"] = overall_score
        
        return overall_score
    
    def generate_detailed_report(self):
        """Generar reporte detallado de pruebas reales"""
        print("\n" + "=" * 70)
        print("📊 REPORTE FINAL - PRUEBAS CON AGENTE REAL")
        print("=" * 70)
        
        overall_score = self.calculate_real_overall_score()
        
        if not self.test_results["connection_test"]:
            print("🚨 CRÍTICO: No se pudo establecer conexión con el agente real")
            print("📝 Recomendación: Verificar configuración y dependencias")
            return False
        
        # Estado general
        if overall_score >= 85:
            status = "🟢 EXCELENTE - COMPLETAMENTE LISTO PARA PRODUCCIÓN"
        elif overall_score >= 75:
            status = "🟡 BUENO - LISTO PARA PRODUCCIÓN CON MONITOREO"
        elif overall_score >= 65:
            status = "🟠 ACEPTABLE - MEJORAS MENORES REQUERIDAS"
        else:
            status = "🔴 CRÍTICO - REQUIERE TRABAJO SIGNIFICATIVO"
        
        print(f"\n🎯 PUNTUACIÓN FINAL: {overall_score:.1f}/100")
        print(f"📈 ESTADO: {status}")
        
        # Detalles por categoría
        print(f"\n📋 RESULTADOS DETALLADOS:")
        
        # Flujos
        if self.test_results["flow_detection"]:
            flow_rate = sum(1 for r in self.test_results["flow_detection"] if r["success"]) / len(self.test_results["flow_detection"]) * 100
            print(f"   🔍 Detección de Flujos: {flow_rate:.1f}% ({sum(1 for r in self.test_results['flow_detection'] if r['success'])}/{len(self.test_results['flow_detection'])})")
        
        # Memoria
        if self.test_results["memory_coherence"]:
            memory_rate = sum(1 for r in self.test_results["memory_coherence"] if r["success"]) / len(self.test_results["memory_coherence"]) * 100
            print(f"   🧠 Coherencia de Memoria: {memory_rate:.1f}% ({sum(1 for r in self.test_results['memory_coherence'] if r['success'])}/{len(self.test_results['memory_coherence'])})")
        
        # Redirección
        if self.test_results["strategic_redirect"]:
            redirect_rate = sum(1 for r in self.test_results["strategic_redirect"] if r["success"]) / len(self.test_results["strategic_redirect"]) * 100
            print(f"   🎯 Redirección Estratégica: {redirect_rate:.1f}% ({sum(1 for r in self.test_results['strategic_redirect'] if r['success'])}/{len(self.test_results['strategic_redirect'])})")
        
        # Conversación
        if self.test_results["conversation_flow"]:
            conversation_rate = sum(1 for r in self.test_results["conversation_flow"] if r["success"]) / len(self.test_results["conversation_flow"]) * 100
            print(f"   💬 Flujo Conversacional: {conversation_rate:.1f}% ({sum(1 for r in self.test_results['conversation_flow'] if r['success'])}/{len(self.test_results['conversation_flow'])})")
        
        # Análisis de fortalezas y debilidades
        print(f"\n💪 FORTALEZAS IDENTIFICADAS:")
        if any(r["success"] for r in self.test_results["strategic_redirect"]):
            print("   ✅ Excelente manejo de consultas fuera de dominio")
        if any(r["success"] for r in self.test_results["flow_detection"]):
            print("   ✅ Buena detección de intenciones del usuario")
        if any(r["success"] for r in self.test_results["conversation_flow"]):
            print("   ✅ Flujo conversacional natural y útil")
        
        print(f"\n⚠️ ÁREAS DE MEJORA:")
        if not all(r["success"] for r in self.test_results["memory_coherence"]):
            print("   🔧 Mejorar persistencia de contexto conversacional")
        if not all(r["success"] for r in self.test_results["flow_detection"]):
            print("   🔧 Optimizar detección de algunas palabras clave")
        
        # Recomendaciones finales
        print(f"\n🎯 RECOMENDACIONES FINALES:")
        if overall_score >= 75:
            print("   ✅ Agente APROBADO para despliegue en producción")
            print("   ✅ Implementar monitoreo continuo post-despliegue")
            print("   ✅ Recopilar métricas reales de usuarios")
        else:
            print("   🚨 Realizar mejoras antes del despliegue")
            print("   🚨 Enfocar esfuerzos en áreas de menor puntuación")
            print("   🚨 Repetir pruebas después de mejoras")
        
        print(f"\n📊 ESTADÍSTICAS DE PRUEBA:")
        print(f"   📝 Total de interacciones probadas: {len(self.conversation_history)}")
        print(f"   👤 ID de usuario de prueba: {self.test_user_id}")
        print(f"   🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("=" * 70)
        
        return overall_score >= 75
    
    def run_complete_real_test(self):
        """Ejecutar suite completa de pruebas con agente real"""
        print(f"🚀 INICIANDO PRUEBAS DE RESILIENCIA CON AGENTE REAL")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test de conexión
        if not self.test_agent_connection():
            print("❌ No se puede continuar sin conexión al agente")
            return False
        
        # Ejecutar todas las pruebas
        flow_success = self.test_real_flow_detection()
        memory_success = self.test_real_memory_coherence()
        redirect_success = self.test_real_strategic_redirect()
        conversation_success = self.test_conversation_flow()
        
        # Generar reporte final
        overall_success = self.generate_detailed_report()
        
        # Guardar logs de conversación para análisis
        try:
            with open(f'test_conversation_log_{self.test_user_id}.json', 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Log de conversación guardado: test_conversation_log_{self.test_user_id}.json")
        except Exception as e:
            print(f"⚠️ No se pudo guardar log: {e}")
        
        return overall_success

def main():
    """Función principal - Ejecutar pruebas reales de resiliencia"""
    print("🔥 INICIANDO PRUEBAS DE RESILIENCIA CON AGENTE REAL")
    print("🎯 Objetivo: Validación final antes de producción")
    print()
    
    # Crear tester
    tester = RealAgentResilienceTest()
    
    # Ejecutar pruebas completas
    success = tester.run_complete_real_test()
    
    if success:
        print("\n✅ RESULTADO FINAL: AGENTE APROBADO PARA PRODUCCIÓN")
        print("🚀 Proceder con deployment en WhatsApp")
    else:
        print("\n❌ RESULTADO FINAL: AGENTE REQUIERE MEJORAS")
        print("🔧 Implementar correcciones antes de producción")
    
    return success

if __name__ == "__main__":
    main()