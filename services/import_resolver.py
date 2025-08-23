# services/import_resolver.py
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class ImportResolver:
    """Resuelve dependencias circulares centralizando imports"""

    def __init__(self):
        self._services_cache = {}
        self._initialized = False

    def initialize_services(self) -> bool:
        """Inicializa todos los servicios una vez"""
        try:
            if self._initialized:
                return True

            # Servicios básicos
            from services.validation_service import get_validation_service
            from services.website_link_service import get_website_link_service
            
            # Nuevos servicios para resolver dependencias
            from services.domain_validation_service import get_domain_validation_service
            from services.topic_detection_service import get_topic_detection_service
            from services.personality_service import get_personality_service
            from services.conversation_integration_service import get_conversation_integration_service
            from services.prompt_service import get_prompt_service
            
            # Servicios opcionales (pueden fallar sin romper el sistema)
            context_service = None
            conversation_handlers = {}
            
            try:
                from services.context_service import get_context_service
                context_service = get_context_service()
            except ImportError:
                logger.warning("Context service no disponible")
            
            try:
                from services.conversation_service import (
                    handle_website_link_request,
                    handle_admin_contact_request,
                    handle_reservation_intent_v3,
                    handle_continuation_response
                )
                conversation_handlers = {
                    'website_link': handle_website_link_request,
                    'admin_contact': handle_admin_contact_request,
                    'reservation_intent': handle_reservation_intent_v3,
                    'continuation': handle_continuation_response
                }
            except ImportError:
                logger.warning("Conversation handlers no disponibles")

            self._services_cache = {
                # Servicios básicos
                'validation_service': get_validation_service(),
                'website_link_service': get_website_link_service(),
                
                # Nuevos servicios de validación y personalidad
                'domain_validation_service': get_domain_validation_service(),
                'topic_detection_service': get_topic_detection_service(),
                'personality_service': get_personality_service(),
                'conversation_integration_service': get_conversation_integration_service(),
                'prompt_service': get_prompt_service(),
                
                # Servicios opcionales
                'context_service': context_service,
                'conversation_handlers': conversation_handlers
            }

            self._initialized = True
            logger.info("ImportResolver inicializado exitosamente con servicios nuevos")
            return True

        except Exception as e:
            logger.error(f"Error inicializando ImportResolver: {e}")
            return False

    def get_service(self, service_name: str) -> Optional[Any]:
        """Obtiene servicio del cache"""
        if not self._initialized:
            self.initialize_services()
        return self._services_cache.get(service_name)

# Instancia global
_import_resolver = ImportResolver()

def get_import_resolver() -> ImportResolver:
    return _import_resolver