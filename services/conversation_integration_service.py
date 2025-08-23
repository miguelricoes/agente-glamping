# services/conversation_integration_service.py
from typing import Tuple, Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class ConversationIntegrationService:
    """Servicio que integra todas las validaciones y mejoras en el flujo de conversación"""

    def __init__(self):
        self.domain_service = None
        self.topic_service = None
        self.personality_service = None
        self.validation_service = None
        self._initialize_services()
        
        logger.info("ConversationIntegrationService inicializado")

    def _initialize_services(self):
        """Inicializa todos los servicios de forma lazy"""
        try:
            from services.domain_validation_service import get_domain_validation_service
            from services.topic_detection_service import get_topic_detection_service
            from services.personality_service import get_personality_service
            from services.validation_service import get_validation_service
            
            self.domain_service = get_domain_validation_service()
            self.topic_service = get_topic_detection_service()
            self.personality_service = get_personality_service()
            self.validation_service = get_validation_service()
            
            logger.info("Servicios de integración inicializados exitosamente")
            
        except Exception as e:
            logger.error(f"Error inicializando servicios de integración: {e}")

    def process_user_message_enhanced(self, message: str, user_state: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Procesa un mensaje del usuario con todas las validaciones y mejoras integradas
        
        Returns:
            Tuple[bool, str, Dict]: (should_continue, response_or_redirect, metadata)
        """
        try:
            metadata = {
                "validation_status": "unknown",
                "topic_detected": None,
                "personality_applied": False,
                "requires_ai": False,
                "redirect_reason": None
            }
            
            # 1. VALIDACIÓN DE DOMINIO
            if self.domain_service:
                is_valid, reason, redirect_suggestion = self.domain_service.validate_domain(message)
                metadata["validation_status"] = "valid" if is_valid else reason
                
                if not is_valid:
                    if reason == "prohibited_content":
                        response = self.domain_service.get_rejection_response("prohibited_content", message)
                        if self.personality_service:
                            response = self.personality_service.apply_personality_to_response(response, "error")
                            metadata["personality_applied"] = True
                        return False, response, metadata
                    
                    elif reason == "redirect_opportunity" and redirect_suggestion:
                        metadata["redirect_reason"] = "topic_redirect"
                        return False, redirect_suggestion, metadata
                    
                    elif reason == "out_of_domain":
                        response = self.domain_service.get_rejection_response("out_of_domain", message)
                        if self.personality_service:
                            response = self.personality_service.apply_personality_to_response(response, "redirect")
                            metadata["personality_applied"] = True
                        return False, response, metadata
            
            # 2. DETECCIÓN DE TEMAS Y REDIRECCIÓN INTELIGENTE
            if self.topic_service:
                needs_redirect, detected_topic, connection, redirect_response = self.topic_service.detect_topic_and_redirect(message)
                metadata["topic_detected"] = detected_topic
                
                if needs_redirect and redirect_response:
                    metadata["redirect_reason"] = "smart_topic_redirect"
                    metadata["topic_connection"] = connection
                    return False, redirect_response, metadata
            
            # 3. ANÁLISIS DE COMPLEJIDAD PARA DETERMINAR SI NECESITA AGENTE IA
            if self.domain_service:
                analysis = self.domain_service.analyze_query_complexity(message)
                metadata["requires_ai"] = analysis.get("needs_ai_agent", False)
                metadata["complexity_score"] = analysis.get("complexity_score", 0)
            
            # 4. Si llegamos aquí, la consulta es válida y debe continuar el procesamiento normal
            return True, "", metadata
            
        except Exception as e:
            logger.error(f"Error procesando mensaje mejorado: {e}")
            return True, "", {"error": str(e)}

    def enhance_response_with_personality(self, response: str, context: str = "") -> str:
        """Aplica personalidad a una respuesta"""
        try:
            if self.personality_service:
                return self.personality_service.apply_personality_to_response(response, context)
            return response
        except Exception as e:
            logger.error(f"Error aplicando personalidad: {e}")
            return response

    def get_enhanced_greeting(self, user_id: str = "") -> str:
        """Obtiene saludo mejorado con personalidad"""
        try:
            if self.personality_service:
                greetings = self.personality_service.get_greeting_variations()
                # Rotar saludos para variedad
                import hashlib
                hash_index = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % len(greetings)
                return greetings[hash_index]
            return "¡Hola! ¿En qué puedo ayudarte con información del glamping?"
        except Exception as e:
            logger.error(f"Error obteniendo saludo mejorado: {e}")
            return "¡Hola! ¿En qué puedo ayudarte?"

    def get_enhanced_error_response(self, error_type: str = "general") -> str:
        """Obtiene respuesta de error mejorada con personalidad"""
        try:
            if self.personality_service:
                error_responses = self.personality_service.get_error_responses()
                return error_responses.get(error_type, error_responses["general"])
            return "Disculpa, hubo un error. ¿En qué puedo ayudarte?"
        except Exception as e:
            logger.error(f"Error obteniendo respuesta de error mejorada: {e}")
            return "Disculpa, hubo un error. ¿En qué puedo ayudarte?"

    def enhance_menu_response(self, option: str, response: str) -> str:
        """Mejora respuesta del menú con personalidad"""
        try:
            if self.personality_service:
                return self.personality_service.enhance_menu_response(option, response)
            return response
        except Exception as e:
            logger.error(f"Error mejorando respuesta del menú: {e}")
            return response

    def should_activate_ai_agent(self, message: str, user_state: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determina si debe activar el agente IA basándose en validaciones integradas
        
        Returns:
            Tuple[bool, str]: (should_activate, reason)
        """
        try:
            # Usar validation_service actualizado que ya integra las nuevas validaciones
            if self.validation_service:
                should_activate, trigger_type, context = self.validation_service.detect_auto_ai_activation(message)
                return should_activate, trigger_type
            
            # Fallback usando domain_service directamente
            if self.domain_service:
                analysis = self.domain_service.analyze_query_complexity(message)
                return analysis.get("needs_ai_agent", False), "complexity_analysis"
            
            return False, "no_validation_service"
            
        except Exception as e:
            logger.error(f"Error determinando activación de agente IA: {e}")
            return False, f"error: {e}"

    def create_enhanced_contextual_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Crea prompt contextual mejorado con personalidad"""
        try:
            if self.personality_service:
                return self.personality_service.create_contextual_prompt(user_input, context)
            
            # Fallback básico
            return f"Usuario pregunta: {user_input}\n\nResponde de manera completa y útil."
            
        except Exception as e:
            logger.error(f"Error creando prompt contextual mejorado: {e}")
            return f"Usuario pregunta: {user_input}\n\nResponde de manera completa y útil."

    def get_follow_up_suggestions(self, last_response: str, detected_topic: str = None) -> list:
        """Obtiene sugerencias de seguimiento inteligentes"""
        try:
            if self.topic_service and detected_topic:
                return self.topic_service.get_follow_up_suggestions(detected_topic)
            
            # Sugerencias genéricas
            return [
                "¿Te gustaría conocer más detalles?",
                "¿Tienes alguna pregunta específica?",
                "¿En qué más puedo ayudarte?"
            ]
            
        except Exception as e:
            logger.error(f"Error obteniendo sugerencias de seguimiento: {e}")
            return []

    def add_closure_if_appropriate(self, response: str, is_final_response: bool = False) -> str:
        """Agrega frase de cierre apropiada si es necesario"""
        try:
            if is_final_response and self.personality_service:
                closures = self.personality_service.get_closure_phrases()
                import random
                closure = random.choice(closures)
                return f"{response}\n\n{closure}"
            return response
        except Exception as e:
            logger.error(f"Error agregando cierre: {e}")
            return response

    def get_health_status(self) -> Dict[str, Any]:
        """Obtiene estado de salud del servicio de integración"""
        return {
            "service_name": "ConversationIntegrationService",
            "domain_service_available": self.domain_service is not None,
            "topic_service_available": self.topic_service is not None,
            "personality_service_available": self.personality_service is not None,
            "validation_service_available": self.validation_service is not None,
            "status": "healthy" if all([
                self.domain_service, self.topic_service, 
                self.personality_service, self.validation_service
            ]) else "degraded"
        }

# Instancia global
_integration_service = ConversationIntegrationService()

def get_conversation_integration_service() -> ConversationIntegrationService:
    return _integration_service