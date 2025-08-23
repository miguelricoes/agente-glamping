# Servicio de contexto inteligente para el agente glamping
# Maneja la memoria contextual y decisiones de activación del agente IA

import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class ContextService:
    """
    Servicio de contexto inteligente que maneja:
    - Memoria de acciones previas
    - Generación de respuestas contextuales
    - Decisiones de activación del agente IA
    """
    
    def __init__(self):
        """Inicializar servicio de contexto"""
        self.user_contexts = {}  # Cache en memoria para contextos de usuario
        logger.info("Inicializando ContextService", 
                   extra={"component": "context_service", "phase": "startup"})
    
    def remember_context(self, user_id: str, action: str, data: dict) -> None:
        """
        Guarda contexto de la última acción
        
        Args:
            user_id: ID del usuario
            action: Tipo de acción realizada
            data: Datos asociados a la acción
        """
        try:
            context_data = {
                'action': action,
                'data': data,
                'timestamp': datetime.utcnow().isoformat(),
                'interactions_count': self.user_contexts.get(user_id, {}).get('interactions_count', 0) + 1
            }
            
            self.user_contexts[user_id] = context_data
            
            logger.info(f"Contexto guardado para usuario {user_id}: {action}", 
                       extra={"component": "context_service", "user_id": user_id, "action": action})
                       
        except Exception as e:
            logger.error(f"Error guardando contexto para {user_id}: {e}", 
                        extra={"component": "context_service", "user_id": user_id})
    
    def get_continuation_response(self, user_id: str, user_input: str) -> Optional[str]:
        """
        Genera respuesta basada en contexto previo
        
        Args:
            user_id: ID del usuario
            user_input: Entrada del usuario
            
        Returns:
            Respuesta contextual o None si no aplica
        """
        try:
            user_input_lower = user_input.lower().strip()
            
            # Obtener contexto del usuario
            context = self.user_contexts.get(user_id, {})
            if not context:
                return None
            
            last_action = context.get('action', '')
            last_data = context.get('data', {})
            
            # Respuestas afirmativas
            if user_input_lower in ['sí', 'si', 'yes', 'claro', 'por supuesto', 'dale', 'ok']:
                return self._generate_affirmative_response(last_action, last_data)
            
            # Respuestas de solicitud de más información
            elif any(pattern in user_input_lower for pattern in ['más', 'detalles', 'información', 'cuéntame']):
                return self._generate_detail_response(last_action, last_data, user_input)
            
            # Respuestas de cambio de tema
            elif any(pattern in user_input_lower for pattern in ['otro', 'diferente', 'cambiar']):
                return self._generate_alternative_response(last_action, last_data)
                
            return None
            
        except Exception as e:
            logger.error(f"Error generando respuesta de continuación: {e}", 
                        extra={"component": "context_service", "user_id": user_id})
            return None
    
    def should_activate_ai_agent(self, user_input: str, context: str) -> bool:
        """
        Decide si activar agente IA basado en contexto
        
        Args:
            user_input: Entrada del usuario
            context: Contexto actual
            
        Returns:
            True si debe activar el agente IA
        """
        try:
            # PRIMERA PRIORIDAD: Usar intelligent_trigger_service para detección automática
            try:
                from services.intelligent_trigger_service import get_intelligent_trigger_service
                trigger_service = get_intelligent_trigger_service()
                should_auto_activate, trigger_type, rag_context = trigger_service.analyze_message(user_input)
                
                if should_auto_activate:
                    logger.info(f"IA activada por intelligent_trigger_service: {trigger_type}", 
                               extra={"component": "context_service", "trigger": trigger_type, "rag_context": rag_context})
                    return True
            except Exception as e:
                logger.warning(f"Error en intelligent_trigger_service: {e}")
            
            # SEGUNDA PRIORIDAD: Patrones específicos de domos y consultas
            user_input_lower = user_input.lower().strip()
            
            ai_required_patterns = [
                r'cuéntame.*sobre.*domo',
                r'más información.*domo',
                r'detalles.*domo.*\w+',
                r'características.*domo',
                r'qué.*incluye.*domo',
                r'precio.*domo.*\w+',
                r'disponibilidad.*domo.*\w+',
                r'diferencias.*entre.*domos',
                r'comparar.*domos',
                r'cuál.*domo.*mejor',
                r'recomienda.*domo',
                r'servicios.*específicos',
                r'actividades.*disponibles',
                r'políticas.*detalladas',
                r'ubicación.*exacta',
                r'cómo.*llegar',
                r'polaris',
                r'aurora',
                r'quasar',
                r'cassiopeia',
                r'antares',
                r'sirius',
                r'centaury',
                r'características.*jacuzzi',
                r'amenidades',
                r'jacuzzi',
                r'información.*del.*domo'
            ]
            
            # Verificar patrones específicos
            for pattern in ai_required_patterns:
                if re.search(pattern, user_input_lower):
                    logger.info(f"Agente IA requerido - patrón detectado: {pattern}", 
                               extra={"component": "context_service", "pattern": pattern})
                    return True
            
            # TERCERA PRIORIDAD: Consultas complejas
            if len(user_input.split()) > 10:  # Consultas largas
                logger.info("Agente IA requerido - consulta compleja detectada", 
                           extra={"component": "context_service", "input_length": len(user_input.split())})
                return True
            
            # Preguntas con múltiples aspectos
            multiple_aspect_keywords = ['y', 'también', 'además', 'qué más', 'otras']
            if any(keyword in user_input_lower for keyword in multiple_aspect_keywords):
                logger.info("Agente IA requerido - múltiples aspectos detectados", 
                           extra={"component": "context_service"})
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error decidiendo activación de agente IA: {e}", 
                        extra={"component": "context_service"})
            return False
    
    def _generate_affirmative_response(self, last_action: str, last_data: dict) -> Optional[str]:
        """Genera respuesta para confirmaciones afirmativas"""
        try:
            if last_action == 'showed_domos' or last_action == 'showed_domos_menu':
                return "¿Sobre cuál domo específico te gustaría saber más? Tenemos:\n🏠 **Antares** - Domo premium\n⭐ **Polaris** - Domo estándar\n✨ **Sirius** - Domo económico\n🌟 **Centaury** - Domo familiar"
            
            elif last_action == 'showed_services_menu':
                return "¿Qué servicios específicos te interesan más?\n🛏️ **Servicios incluidos** - Lo que viene con tu estadía\n🎯 **Actividades adicionales** - Experiencias extras que puedes agregar"
            
            elif last_action == 'showed_availability':
                return "¿Te gustaría proceder con la reserva o necesitas consultar otras fechas?"
            
            elif last_action == 'showed_policies':
                return "¿Sobre qué política específica necesitas más detalles? Puedo explicarte sobre cancelaciones, mascotas o privacidad."
            
            return "¿En qué más puedo ayudarte? Puedo darte información detallada sobre cualquier aspecto del glamping."
            
        except Exception as e:
            logger.error(f"Error generando respuesta afirmativa: {e}")
            return None
    
    def _generate_detail_response(self, last_action: str, last_data: dict, user_input: str) -> Optional[str]:
        """Genera respuesta para solicitudes de más detalles"""
        try:
            if 'domo' in user_input.lower():
                return "Te puedo dar información detallada sobre cualquier domo. ¿Cuál te interesa? Antares, Polaris, Sirius o Centaury?"
            
            elif 'servicio' in user_input.lower():
                return "¿Qué servicios específicos quieres conocer? Puedo contarte sobre servicios incluidos, actividades adicionales, o servicios de bienestar."
            
            elif 'precio' in user_input.lower():
                return "Te puedo dar información detallada de precios. ¿Para qué domo y qué fechas necesitas la cotización?"
            
            return "¿Sobre qué aspecto específico del glamping necesitas más información?"
            
        except Exception as e:
            logger.error(f"Error generando respuesta de detalles: {e}")
            return None
    
    def _generate_alternative_response(self, last_action: str, last_data: dict) -> Optional[str]:
        """Genera respuesta para solicitudes de alternativas"""
        try:
            if last_action == 'showed_domos_menu':
                return "¿Qué otro tipo de información te interesa? Puedo contarte sobre:\n📅 **Disponibilidad** - Fechas libres\n🛎️ **Servicios** - Qué incluimos\n🎯 **Actividades** - Experiencias disponibles\n📋 **Políticas** - Términos y condiciones"
            
            elif last_action == 'showed_availability':
                return "¿Te gustaría ver otras fechas disponibles o prefieres información sobre otro tema como servicios o actividades?"
            
            return "¿Qué otro tema te interesa? Puedo ayudarte con domos, servicios, actividades, políticas o hacer una reserva."
            
        except Exception as e:
            logger.error(f"Error generando respuesta alternativa: {e}")
            return None
    
    def get_user_context(self, user_id: str) -> dict:
        """Obtiene el contexto completo de un usuario"""
        return self.user_contexts.get(user_id, {})
    
    def clear_user_context(self, user_id: str) -> None:
        """Limpia el contexto de un usuario"""
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
            logger.info(f"Contexto limpiado para usuario {user_id}", 
                       extra={"component": "context_service", "user_id": user_id})
    
    def update_user_state_with_context(self, user_state: dict, action: str, data: dict) -> None:
        """Actualiza el estado del usuario con información de contexto"""
        try:
            user_state['previous_context'] = action
            user_state['last_action'] = action
            user_state['waiting_for_continuation'] = True
            
            logger.info(f"Estado de usuario actualizado con contexto: {action}", 
                       extra={"component": "context_service", "action": action})
                       
        except Exception as e:
            logger.error(f"Error actualizando estado con contexto: {e}", 
                        extra={"component": "context_service"})


# Instancia global del servicio
context_service = ContextService()

def get_context_service() -> ContextService:
    """Obtener instancia global del servicio de contexto"""
    return context_service