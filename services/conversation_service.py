# Unified conversation service - Eliminates duplication between WhatsApp and Chat endpoints
# This service contains the core conversation logic that was duplicated

from datetime import datetime
from typing import Tuple, Dict, Any, Union
from utils.logger import get_logger, log_conversation, log_error

# Inicializar logger para este módulo
logger = get_logger(__name__)

def replace_generic_menu_response(agent_response: str, user_input: str) -> str:
    """Replace generic menu responses from AI agent with specific ones"""
    
    # Check if this is a generic menu response
    is_generic_menu = (
        "Has seleccionado la opción" in agent_response and 
        "¿En qué puedo ayudarte específicamente?" in agent_response
    )
    
    if not is_generic_menu:
        return agent_response
    
    # Extract option number from user input
    option = None
    for i in range(1, 9):
        if str(i) in user_input:
            option = str(i)
            break
    
    if not option:
        return agent_response
    
    
    # Return specific response based on option
    specific_responses = {
        "1": """📍 **¿Qué te gustaría saber sobre nuestra información general?**
        
🏕️ Puedo contarte sobre:
• **Concepto** - Qué es Glamping Brillo de Luna
• **Ubicación** - Dónde nos encontramos
• **Contacto** - Cómo comunicarte con nosotros
• **Historia** - Nuestra experiencia en glamping
• **Certificaciones** - Nuestros estándares de calidad

💬 ¿Qué información específica necesitas?""",

        "2": """🏠 **¿Qué quieres saber de los domos?**
        
🌟 Puedo contarte sobre:
• **Tipos de domos** - Antares, Polaris, Sirius, Centaury
• **Características** - Qué incluye cada domo
• **Precios** - Tarifas por noche y temporada
• **Capacidad** - Cuántas personas pueden hospedarse
• **Amenidades** - Servicios incluidos en cada domo
• **Vistas** - Qué puedes ver desde cada domo

💬 ¿Qué aspecto de los domos te interesa más?""",

        "3": """📅 **¿Para qué fechas quieres consultar disponibilidad?**
        
🗓️ Puedo ayudarte con:
• **Fechas específicas** - Verifica si están libres
• **Rangos de fechas** - Encuentra opciones disponibles
• **Temporadas** - Conoce las mejores épocas
• **Promociones** - Descuentos por fechas específicas
• **Reserva inmediata** - Si las fechas están disponibles

💬 Dime las fechas que te interesan (DD/MM/AAAA)""",

        "4": """🛎️ **¿Qué servicios te gustaría conocer?**
        
✨ Puedo contarte sobre:
• **Servicios incluidos** - Qué está incluido en tu estadía
• **Servicios adicionales** - Experiencias extras disponibles
• **Alimentación** - Opciones de desayuno y comidas
• **Amenidades** - WiFi, parqueadero, instalaciones
• **Actividades** - Qué puedes hacer durante tu estadía

💬 ¿Sobre qué servicios específicos quieres información?""",

        "5": """🎯 **¿Qué actividades adicionales te interesan?**
        
🌟 Puedo contarte sobre:
• **Experiencias de naturaleza** - Senderismo, observación de aves
• **Actividades deportivas** - Ciclismo, rappel, canopy
• **Bienestar** - Yoga, masajes, spa
• **Gastronomía** - Cenas románticas, clases de cocina
• **Precios** - Costos de cada actividad
• **Reservas** - Cómo reservar actividades

💬 ¿Qué tipo de actividades buscas para tu estadía?""",

        "6": """📋 **¿Qué políticas necesitas conocer?**
        
📄 Puedo explicarte sobre:
• **Cancelaciones** - Políticas de cancelación y reembolsos
• **Mascotas** - Condiciones para viajar con tu mascota
• **Check-in/Check-out** - Horarios y procedimientos
• **Normas generales** - Reglas de convivencia
• **Pagos** - Métodos de pago aceptados
• **Seguros** - Coberturas y responsabilidades

💬 ¿Sobre qué política específica tienes dudas?""",

        "7": """📸 **¿Qué imágenes te gustaría ver?**
        
🌟 Puedo mostrarte:
• **Galería de domos** - Fotos de todos nuestros domos
• **Instalaciones** - Áreas comunes y servicios
• **Entorno natural** - Paisajes y vistas
• **Actividades** - Fotos de experiencias disponibles
• **Enlaces directos** - Links a nuestras galerías online

💬 ¿Qué fotos específicas del glamping quieres ver?""",

        "8": """♿ **¿Qué necesitas saber sobre accesibilidad?**
        
🏠 Puedo informarte sobre:
• **Domos adaptados** - Instalaciones para movilidad reducida
• **Accesos** - Rampas y senderos accesibles
• **Baños** - Facilidades adaptadas
• **Servicios especiales** - Asistencia disponible
• **Reservas** - Cómo solicitar acomodaciones especiales

💬 ¿Qué tipo de información de accesibilidad necesitas?"""
    }
    
    return specific_responses.get(option, agent_response)

def add_message_to_memory(memory, user_message: str, ai_response: str):
    """Unified function to add messages to memory with fallback compatibility and token limits"""
    
    # Limitar longitud de mensajes para reducir tokens
    MAX_MESSAGE_LENGTH = 200
    user_message = user_message[:MAX_MESSAGE_LENGTH] if len(user_message) > MAX_MESSAGE_LENGTH else user_message
    ai_response = ai_response[:MAX_MESSAGE_LENGTH] if len(ai_response) > MAX_MESSAGE_LENGTH else ai_response
    
    try:
        from langchain.schema import HumanMessage, AIMessage
        memory.chat_memory.add_message(HumanMessage(content=user_message))
        memory.chat_memory.add_message(AIMessage(content=ai_response))
        
        # Limitar historial de memoria (mantener solo últimos 10 mensajes)
        if hasattr(memory.chat_memory, 'messages') and len(memory.chat_memory.messages) > 20:  # 10 pares
            memory.chat_memory.messages = memory.chat_memory.messages[-20:]
            
    except (ImportError, AttributeError):
        try:
            memory.chat_memory.add_user_message(user_message)
            memory.chat_memory.add_ai_message(ai_response)
        except:
            pass

def is_new_conversation(memory) -> bool:
    """Check if this is a new conversation based on memory content"""
    if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
        # If only has 2 messages (system + assistant_response) it's a new conversation
        if len(memory.chat_memory.messages) <= 2:
            return True
    return False

def handle_greeting_new_conversation(memory, user_message: str, is_greeting_message_func, get_welcome_menu_func, save_user_memory_func, user_id: str) -> Tuple[bool, str]:
    """Handle greeting in new conversation - returns (handled, response)"""
    if is_greeting_message_func(user_message) and is_new_conversation(memory):
        welcome_message = get_welcome_menu_func()
        add_message_to_memory(memory, user_message, welcome_message)
        save_user_memory_func(user_id, memory)
        return True, welcome_message
    return False, ""

def handle_menu_selection_unified(user_message: str, user_state: dict, memory, qa_chains, 
                                handle_menu_selection_func, save_user_memory_func, user_id: str, 
                                is_menu_selection_func, validation_service=None) -> Tuple[bool, Union[str, dict]]:
    """Unified menu selection handling with improved flexibility - returns (handled, response)"""
    
    try:
        logger.info(f"handle_menu_selection_unified called with: user_message='{user_message}', current_flow='{user_state.get('current_flow')}'", 
                   extra={"component": "conversation_service"})
        
        # VALIDACIÓN DE PARÁMETROS ANTES DE PROCEDER
        if validation_service is None:
            logger.warning("validation_service no disponible, usando fallback", 
                          extra={"component": "conversation_service"})
            # Usar fallback service comprensivo en lugar del básico
            from services.fallback_service import detect_topic_and_provide_fallback
            handled, fallback_response, topic = detect_topic_and_provide_fallback(user_message)
            
            if handled:
                logger.info(f"Fallback service manejó consulta: {topic}", 
                           extra={"component": "conversation_service", "topic": topic})
                return True, fallback_response
            else:
                # Si no se detectó tema específico, usar fallback básico como último recurso
                from routes.whatsapp_routes import handle_fallback_menu_response
                fallback_response = handle_fallback_menu_response(user_message, user_state.get('current_flow', 'none'))
                return True, fallback_response
        
        if not user_message or not isinstance(user_message, str):
            logger.warning(f"user_message inválido: {user_message}", 
                          extra={"component": "conversation_service"})
            return False, "Por favor, envía un mensaje válido."
        
        if not user_state or not isinstance(user_state, dict):
            logger.warning("user_state inválido, inicializando nuevo estado", 
                          extra={"component": "conversation_service"})
            user_state = {"current_flow": "none"}
        
        # Always use improved menu service - create validation service if not provided
        if validation_service is None:
            from services.validation_service import ValidationService
            validation_service = ValidationService()
    
        is_menu_sel = validation_service.is_menu_selection(user_message)
        current_flow_none = user_state["current_flow"] == "none"
        
        if is_menu_sel and current_flow_none:
            try:
                logger.info("Using improved menu service", extra={"component": "conversation_service"})
                # Import and use the new menu service
                from services.menu_service import create_menu_service
                menu_service = create_menu_service(qa_chains, validation_service)
                menu_response = menu_service.handle_menu_selection(user_message, user_state)
                
                # DEBUGGING: Log what menu_service returned
                logger.info(f"🔍 CONVERSATION DEBUG: menu_response type={type(menu_response)}, is_dict={isinstance(menu_response, dict)}", 
                           extra={"component": "conversation_service", "user_message": user_message[:30]})
                
                # Handle dictionary response (option 3 - availability, option 1 - domos followup, option 2 - servicios followup)
                if isinstance(menu_response, dict):
                    if "set_waiting_for_availability" in menu_response:
                        user_state["waiting_for_availability"] = True
                        user_state["current_flow"] = "availability"
                    elif "set_waiting_for_domos_followup" in menu_response:
                        user_state["waiting_for_domos_followup"] = True
                        user_state["current_flow"] = "domos_followup"
                    elif "set_waiting_for_servicios_followup" in menu_response:
                        user_state["waiting_for_servicios_followup"] = True
                        user_state["current_flow"] = "servicios_followup"
                        
                    add_message_to_memory(memory, user_message, menu_response["message"])
                    save_user_memory_func(user_id, memory)
                    return True, menu_response
                else:
                    # String response
                    add_message_to_memory(memory, user_message, menu_response)
                    save_user_memory_func(user_id, memory)
                    return True, menu_response
                    
            except Exception as e:
                logger.error(f"Error en manejo de menú mejorado: {e}", 
                            extra={"component": "conversation_service", "user_id": user_id})
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}", 
                            extra={"component": "conversation_service"})
                # Fallback to original menu handling
    
        # Fallback to original menu selection handling
        logger.info("Falling back to original menu selection handling", extra={"component": "conversation_service"})
        if is_menu_selection_func(user_message) and user_state["current_flow"] == "none":
            try:
                logger.info("Using fallback menu service", extra={"component": "conversation_service"})
                menu_response = handle_menu_selection_func(user_message, qa_chains)
                
                # Handle dictionary response (option 3)
                if isinstance(menu_response, dict):
                    message_text = menu_response["message"]
                    if menu_response.get("set_waiting_for_availability"):
                        user_state["waiting_for_availability"] = True
                    add_message_to_memory(memory, user_message, message_text)
                    save_user_memory_func(user_id, memory)
                    return True, menu_response
                else:
                    # Normal string response
                    add_message_to_memory(memory, user_message, menu_response)
                    save_user_memory_func(user_id, memory)
                    return True, menu_response
                    
            except Exception as e:
                logger.error(f"Error en manejo de menú: {e}", extra={"phase": "conversation", "component": "menu_selection"})
                error_response = "Disculpa, hubo un error procesando tu selección. ¿Podrías intentar de nuevo?"
                return True, error_response
    
        return False, ""
    
    except Exception as e:
        logger.error(f"Error crítico en handle_menu_selection_unified: {e}", 
                    extra={"component": "conversation_service"})
        # Importar función de fallback desde routes
        from routes.whatsapp_routes import generate_simple_menu_response
        fallback_response = generate_simple_menu_response('menu_principal')
        return True, fallback_response

def detect_cancellation_intent(user_message: str) -> bool:
    """
    Detecta si el usuario quiere cancelar o salir del flujo actual.
    Integrado en máquina de estados para manejo robusto.
    """
    cancellation_patterns = [
        # Cancelación directa
        "no quiero", "ya no quiero", "no me interesa", "cancelar", "salir",
        # Disculpas y retroceso
        "perdón", "perdon", "mejor no", "olvídalo", "olvidalo", "déjalo", "dejalo",
        # Negación educada
        "no gracias", "no, gracias", "cambio de opinión", "cambio de opinion",
        # Navegación
        "regresa", "regresar", "volver", "atrás", "atras", "menú", "menu",
        "inicio", "empezar de nuevo", "otra cosa", "algo más", "algo mas"
    ]
    
    message_lower = user_message.lower().strip()
    return any(pattern in message_lower for pattern in cancellation_patterns)

def reset_user_state_to_main(user_state: dict, clear_data: bool = True) -> None:
    """
    Resetea el estado del usuario al estado principal (STATE_MAIN).
    Parte de la máquina de estados para manejo de cancelaciones.
    """
    user_state["current_flow"] = "none"
    user_state["waiting_for_availability"] = False
    user_state["waiting_for_availability_confirmation"] = False
    user_state["reserva_step"] = 0
    
    if clear_data:
        user_state["reserva_data"] = {}
        # Limpiar cualquier dato específico del flujo
        keys_to_clear = [k for k in user_state.keys() if k.startswith("temp_")]
        for key in keys_to_clear:
            del user_state[key]

def detect_rag_response_pattern(agent_response: str) -> dict:
    """
    Detecta si una respuesta del agente LLM es una respuesta RAG que puede generar follow-up.
    Retorna información sobre el contexto detectado para mantener estado conversacional.
    """
    context_info = {"has_followup_potential": False, "topic": None, "entities": [], "flow_type": None}
    
    response_lower = agent_response.lower()
    
    # Detectar respuestas sobre domos que terminan con pregunta de seguimiento
    # Usar patrones más flexibles sin acentos y caracteres especiales
    domo_patterns = [
        "te gustaria saber algo mas especifico sobre nuestros domos",
        "quieres mas informacion especifica",
        "necesitas mas detalles sobre",
        "responde si si quieres mas informacion",
        "responde \"si\" si quieres",
        "quieres saber algo mas especifico",
        "te gustaria conocer mas detalles",
        "puedo contarte sobre",
        "un domo en particular"
    ]
    
    if any(pattern in response_lower for pattern in domo_patterns):
        context_info["has_followup_potential"] = True
        context_info["flow_type"] = "rag_followup"
        context_info["topic"] = "domos"
        
        # Extraer nombres de domos mencionados
        domo_names = ["antares", "polaris", "sirius", "centaury"]
        mentioned_domos = [domo for domo in domo_names if domo in response_lower]
        context_info["entities"] = mentioned_domos
        
    # Detectar otros tipos de respuestas RAG con potencial de seguimiento
    elif ("🔍" in agent_response or "💡" in agent_response) and ("más" in response_lower or "específico" in response_lower):
        context_info["has_followup_potential"] = True
        context_info["flow_type"] = "rag_followup"
        context_info["topic"] = "general"
    
    return context_info

def detect_followup_intent(user_message: str, conversation_context: dict) -> bool:
    """
    Detecta si el mensaje del usuario es una respuesta de seguimiento basado en el contexto previo.
    """
    if not conversation_context.get("has_followup_potential"):
        return False
    
    message_lower = user_message.lower().strip()
    
    # Patrones de respuesta afirmativa para seguimiento
    affirmative_patterns = [
        "sí", "si", "yes", "claro", "por favor", "dale", "ok", "está bien", "esta bien",
        "quiero saber más", "quiero más información", "dime más", "cuéntame más",
        "sí, quiero saber", "si, quiero saber", "más detalles", "más información"
    ]
    
    # Patrones de especificidad (mencionar entidades del contexto)
    if conversation_context.get("entities"):
        for entity in conversation_context["entities"]:
            if entity in message_lower:
                return True
    
    # Revisar patrones afirmativos
    return any(pattern in message_lower for pattern in affirmative_patterns)

def enrich_followup_message(user_message: str, conversation_context: dict) -> str:
    """
    Enriquece el mensaje del usuario con contexto para mejorar la respuesta del LLM.
    """
    if not conversation_context.get("has_followup_potential"):
        return user_message
    
    topic = conversation_context.get("topic", "información")
    entities = conversation_context.get("entities", [])
    
    # Construir mensaje enriquecido basado en el contexto
    enriched_parts = [
        f"[CONTEXTO: El usuario previamente preguntó sobre {topic}"
    ]
    
    if entities:
        entities_str = ", ".join(entities)
        enriched_parts.append(f"específicamente mencionando: {entities_str}")
    
    enriched_parts.extend([
        f"y ahora responde: '{user_message}']",
        f"Usuario: {user_message}"
    ])
    
    return " ".join(enriched_parts)

def update_conversation_context(user_state: dict, context_info: dict) -> None:
    """
    Actualiza el estado del usuario con información de contexto conversacional.
    """
    if context_info.get("has_followup_potential"):
        user_state["waiting_for_rag_followup"] = True
        user_state["current_flow"] = "rag_followup"
        user_state["conversation_context"] = context_info
        user_state["context_timestamp"] = datetime.now().isoformat()
    else:
        # Limpiar contexto si no hay potencial de seguimiento
        user_state.pop("waiting_for_rag_followup", None)
        user_state.pop("conversation_context", None)
        user_state.pop("context_timestamp", None)
        if user_state.get("current_flow") == "rag_followup":
            user_state["current_flow"] = "none"

def process_response_and_detect_context(response: str, user_state: dict, session_id: str) -> str:
    """
    Procesa cualquier respuesta y detecta potencial de seguimiento conversacional.
    Esta función debe ser llamada en TODOS los puntos de retorno de respuestas.
    """
    # Detectar si la respuesta puede generar seguimiento
    context_info = detect_rag_response_pattern(response)
    update_conversation_context(user_state, context_info)
    
    if context_info.get("has_followup_potential"):
        logger.info(f"Response set RAG followup context: {context_info.get('topic')} with entities: {context_info.get('entities')}", 
                   extra={"component": "conversation_service", "user_id": session_id})
    
    return response

def handle_rag_followup_unified(user_input: str, user_state: dict, memory, 
                              initialize_agent_safe_func, run_agent_safe_func,
                              save_user_memory_func, session_id: str) -> Tuple[bool, str]:
    """
    Maneja el flujo de seguimiento de respuestas RAG con contexto conversacional.
    """
    # Verificar si estamos en modo de espera de seguimiento RAG
    if not user_state.get("waiting_for_rag_followup") or user_state.get("current_flow") != "rag_followup":
        return False, ""
    
    try:
        conversation_context = user_state.get("conversation_context", {})
        
        # Verificar si es realmente una respuesta de seguimiento
        if not detect_followup_intent(user_input, conversation_context):
            # Si no es un seguimiento, limpiar el contexto y procesar normalmente
            user_state["waiting_for_rag_followup"] = False
            user_state["current_flow"] = "none"
            user_state.pop("conversation_context", None)
            return False, ""
        
        # Enriquecer el mensaje con contexto para mejor respuesta del LLM
        enriched_message = enrich_followup_message(user_input, conversation_context)
        
        logger.info(f"Processing RAG followup with enriched message: {enriched_message}", 
                   extra={"component": "conversation_service"})
        
        # Procesar a través del agente LLM con contexto enriquecido
        agent_response = process_ai_agent(
            enriched_message, memory, [], initialize_agent_safe_func, 
            run_agent_safe_func, save_user_memory_func, session_id, user_state
        )
        
        # Limpiar el contexto de seguimiento después de procesar
        user_state["waiting_for_rag_followup"] = False
        user_state["current_flow"] = "none" 
        user_state.pop("conversation_context", None)
        user_state.pop("context_timestamp", None)
        
        # Guardar en memoria
        add_message_to_memory(memory, user_input, agent_response)
        save_user_memory_func(session_id, memory)
        
        return True, agent_response
        
    except Exception as e:
        logger.error(f"Error procesando RAG followup: {e}", 
                    extra={"component": "conversation_service", "user_id": session_id})
        
        # Limpiar estado en caso de error
        user_state["waiting_for_rag_followup"] = False
        user_state["current_flow"] = "none"
        user_state.pop("conversation_context", None)
        
        return True, "Disculpa, tuve un problema procesando tu respuesta. ¿En qué más puedo ayudarte?"

def handle_cancellation_gracefully(user_message: str, user_state: dict, memory, 
                                 save_user_memory_func, user_id: str) -> Tuple[bool, str]:
    """
    Maneja la cancelación de forma elegante, reseteando estado y proporcionando 
    respuesta amigable según el contexto del flujo actual.
    """
    current_flow = user_state.get("current_flow", "none")
    
    # Generar respuesta contextual según el flujo que se está cancelando
    if current_flow == "availability":
        response = """✅ **Consulta de disponibilidad cancelada**

🏠 **Explora más opciones:**
• Escribe "domos" para ver alojamientos
• Escribe "servicios" para actividades  
• Escribe "menú" para opciones principales

**Puedo ayudarte con:**
• 🏠 **Información de domos** - Características y precios
• 🛎️ **Servicios incluidos** - Qué incluye tu estadía  
• 🎯 **Recomendaciones personalizadas** - Dime qué buscas
• 📞 **Contacto directo** - WhatsApp: +57 305 461 4926

💬 ¿En qué más puedo ayudarte?"""
    
    elif current_flow == "reservation":
        response = """✅ **Proceso de reserva cancelado**

🏠 No hay problema, puedes volver cuando gustes.

**Mientras tanto, puedo ayudarte con:**
• 📅 **Consultar disponibilidad** - Sin compromiso
• 🏠 **Información de domos** - Conoce nuestras opciones
• 💰 **Precios y tarifas** - Costos detallados
• 🎯 **Recomendaciones** - Encuentra tu domo ideal

💬 ¿Qué te gustaría saber?"""
    
    else:
        response = """✅ **Entendido**

🏠 **¿En qué más puedo ayudarte?**

• 🏠 **Domos disponibles** - Tipos y características
• 📅 **Consultar disponibilidad** - Fechas libres
• 🎯 **Recomendaciones personalizadas** - Dime qué buscas
• 📞 **Contacto** - WhatsApp: +57 305 461 4926

💬 Estoy aquí para lo que necesites."""
    
    # Resetear estado a principal
    reset_user_state_to_main(user_state, clear_data=True)
    
    # Guardar estado actualizado
    add_message_to_memory(memory, user_message, response)
    save_user_memory_func(user_id, memory)
    
    logger.info(f"Cancelación manejada gracefully desde flujo: {current_flow}", 
               extra={"component": "conversation_service", "action": "cancellation"})
    
    return True, response

def handle_availability_request_unified(user_message: str, user_state: dict, memory, qa_chains,
                                      handle_availability_request_func, save_user_memory_func, 
                                      user_id: str, validation_service=None) -> Tuple[bool, str]:
    """
    Unified availability request handling with integrated cancellation detection.
    Implementa máquina de estados robusta.
    """
    
    # 🚨 PRIORIDAD 1: Detectar intención de cancelación ANTES de procesar cualquier flujo
    if detect_cancellation_intent(user_message):
        return handle_cancellation_gracefully(user_message, user_state, memory, 
                                            save_user_memory_func, user_id)
    
    # Handle initial availability request
    if user_state.get("waiting_for_availability", False) and user_state["current_flow"] == "availability":
        try:
            if validation_service:
                # Use enhanced menu service for availability handling
                from services.menu_service import create_menu_service
                menu_service = create_menu_service(qa_chains, validation_service)
                availability_response = menu_service.handle_availability_request(user_message, user_state)
            else:
                # Fallback to original function
                availability_response = handle_availability_request_func(user_message)
                user_state["waiting_for_availability"] = False
            
            add_message_to_memory(memory, user_message, availability_response)
            save_user_memory_func(user_id, memory)
            return True, availability_response
            
        except Exception as e:
            logger.error(f"Error procesando consulta de disponibilidad: {e}", extra={"phase": "conversation", "component": "availability"})
            user_state["waiting_for_availability"] = False
            user_state["current_flow"] = "none"
            error_response = "Disculpa, hubo un error procesando tu consulta. ¿Podrías intentar de nuevo?"
            return True, error_response
    
    # Handle availability confirmation (when dates are available)
    if user_state.get("waiting_for_availability_confirmation", False) and user_state["current_flow"] == "availability_confirmation":
        try:
            if validation_service:
                from services.menu_service import create_menu_service
                menu_service = create_menu_service(qa_chains, validation_service)
                confirmation_response = menu_service.handle_availability_confirmation(user_message, user_state)
            else:
                # Simple fallback
                user_state["waiting_for_availability_confirmation"] = False
                user_state["current_flow"] = "none"
                confirmation_response = "Consulta de disponibilidad procesada. ¿En qué más puedo ayudarte?"
            
            add_message_to_memory(memory, user_message, confirmation_response)
            save_user_memory_func(user_id, memory)
            return True, confirmation_response
            
        except Exception as e:
            logger.error(f"Error en confirmación de disponibilidad: {e}", extra={"phase": "conversation", "component": "availability_confirmation"})
            user_state["waiting_for_availability_confirmation"] = False
            user_state["current_flow"] = "none"
            error_response = "Hubo un error procesando tu respuesta. ¿Podrías intentar de nuevo?"
            return True, error_response
    
    # Handle availability alternatives (when dates are not available)
    if user_state.get("waiting_for_availability_alternatives", False) and user_state["current_flow"] == "availability_alternatives":
        try:
            if validation_service:
                from services.menu_service import create_menu_service
                menu_service = create_menu_service(qa_chains, validation_service)
                alternatives_response = menu_service.handle_availability_alternatives(user_message, user_state)
            else:
                # Simple fallback
                user_state["waiting_for_availability_alternatives"] = False
                user_state["current_flow"] = "none"
                alternatives_response = "Búsqueda de fechas alternativas procesada. ¿En qué más puedo ayudarte?"
            
            add_message_to_memory(memory, user_message, alternatives_response)
            save_user_memory_func(user_id, memory)
            return True, alternatives_response
            
        except Exception as e:
            logger.error(f"Error en búsqueda de fechas alternativas: {e}", extra={"phase": "conversation", "component": "availability_alternatives"})
            user_state["waiting_for_availability_alternatives"] = False
            user_state["current_flow"] = "none"
            error_response = "Hubo un error procesando tu respuesta. ¿Podrías intentar de nuevo?"
            return True, error_response
    
    return False, ""

def detect_reservation_intent(user_message: str, button_payload: str = None, user_state: dict = None) -> bool:
    """
    Detect if user wants to make a reservation (updated for Variable 3)
    Now uses the intelligent reservation intent service with user_state awareness
    """
    try:
        # Check button payload intent first
        button_intent = bool(button_payload and "reserva" in button_payload.lower())
        if button_intent:
            return True
        
        # Use the new intelligent service for Variable 3
        from services.reservation_intent_service import get_reservation_intent_service
        reservation_service = get_reservation_intent_service()
        
        # Pass user_state to the service for better context awareness
        return reservation_service.should_start_reservation_flow(user_message, user_state)
        
    except Exception as e:
        logger.error(f"Error detectando intención de reserva: {e}")
        # Fallback to basic detection
        message_lower = user_message.lower()
        return "quiero hacer una reserva" in message_lower or "quiero reservar" in message_lower

def initiate_reservation_flow(user_state: dict, memory, save_user_memory_func, user_id: str) -> str:
    """Initiate reservation flow and return initial message"""
    user_state["current_flow"] = "reserva"
    user_state["reserva_step"] = 1
    user_state["reserva_data"] = {}
    
    initial_message = """🏕️ **NUEVA RESERVA GLAMPING BRILLO DE LUNA** ✨

📋 **ENVÍA TUS DATOS EN FORMATO DE LISTA (EN ESTE ORDEN):**

1️⃣ **Nombre completo**
2️⃣ **Número de teléfono/WhatsApp**  
3️⃣ **Email/correo electrónico**
4️⃣ **Número de personas** (1, 2, 3...)
5️⃣ **Fecha de entrada** (DD/MM/AAAA)
6️⃣ **Fecha de salida** (DD/MM/AAAA)
7️⃣ **Domo preferido** (Antares, Polaris, Sirius, Centaury)
8️⃣ **Servicios adicionales** (masajes, spa, ninguno)
9️⃣ **Método de pago** (efectivo, tarjeta, transferencia)
🔟 **Observaciones** (opcional - cualquier información adicional)

💬 **FORMATO CORRECTO - Envía cada dato en una línea:**

Nombre: Juan Pérez
Teléfono: 3001234567
Email: juan@email.com
Personas: 2
Entrada: 15/12/2024
Salida: 17/12/2024
Domo: Antares
Servicios: masajes
Pago: efectivo
Observaciones: celebración aniversario

¿Puedes enviarme tus datos en este formato? 😊"""
    
    save_user_memory_func(user_id, memory)
    return initial_message

def process_reservation_step_1(user_message: str, user_state: dict, memory, save_user_memory_func, 
                             user_id: str, parse_reservation_details_func, 
                             validate_and_process_reservation_data_func, 
                             calcular_precio_reserva_func) -> str:
    """Process reservation step 1 (data collection) and return response with cancellation detection"""
    
    # 🚨 CANCELATION CHECK: Detectar cancelación antes de procesar reserva
    if detect_cancellation_intent(user_message):
        handled, response = handle_cancellation_gracefully(
            user_message, user_state, memory, save_user_memory_func, user_id
        )
        return response
    
    try:
        logger.info("Procesando step 1 de reserva", 
                   extra={"component": "conversation_service", "user_id": user_id})
        
        # Parse reservation details
        parse_success, parsed_data, parse_message = parse_reservation_details_func(user_message)
        
        if not parse_success:
            # Parsing failed - provide helpful feedback
            return f"""❌ **No pude procesar tu información de reserva**

🔍 **Problema detectado:** {parse_message}

📋 **Recuerda incluir estos datos:**
• **Correo electrónico** (ejemplo: maria@gmail.com)
• **Teléfono/WhatsApp** (ejemplo: 3001234567)  
• **Cantidad de huéspedes** (ejemplo: 2 personas)
• **Domo preferido** (Antares, Polaris, Sirius, Centaury)
• **Fecha entrada** (ejemplo: 15/12/2024)
• **Fecha salida** (ejemplo: 17/12/2024)
• **Método de pago** (efectivo, tarjeta, transferencia, Nequi)
• **Servicios** (paseos, masajes, caminatas)

💡 **Ejemplo completo:**
"Reserva para Juan Pérez, correo juan@email.com, teléfono 3001234567, 2 huéspedes, domo Antares, entrada 15/12/2024, salida 17/12/2024, pago efectivo, servicios: masajes"

✏️ **Envía toda la información corregida en un solo mensaje** 😊"""
        
        # Validate processed data
        validation_success, processed_data, validation_errors = validate_and_process_reservation_data_func(parsed_data, user_id)
        
        if not validation_success:
            # Validation failed - provide specific errors
            error_msg = "❌ **Hay problemas con algunos datos proporcionados:**\n\n"
            
            for i, error in enumerate(validation_errors, 1):
                error_msg += f"• **Error {i}:** {error}\n"
            
            error_msg += f"""
🔧 **Por favor, corrige estos problemas y envía la información completa nuevamente:**

📋 **Datos que necesito:**
• **Correo electrónico** (formato: usuario@dominio.com)
• **Teléfono/WhatsApp** (formato: 3001234567)  
• **Cantidad de huéspedes** (número: 1, 2, 3...)
• **Domo preferido** (opciones: Antares, Polaris, Sirius, Centaury)
• **Fecha entrada** (formato: DD/MM/AAAA)
• **Fecha salida** (formato: DD/MM/AAAA)
• **Método de pago** (opciones: efectivo, tarjeta, transferencia, Nequi)
• **Servicios** (opciones: paseos, masajes, caminatas)

✏️ **Envía todos los datos corregidos en un solo mensaje** 😊"""
            
            return error_msg
        
        # Success - create confirmation message using ReservationService
        user_state["reserva_data"] = processed_data
        
        # Generate reservation summary
        from services.reservation_service import ReservationService
        reservation_service = ReservationService()
        summary = reservation_service.create_reservation_summary(processed_data)
        
        # Calculate price if possible
        price_info = ""
        if processed_data.get('monto_total'):
            price_info = f"\n💰 **Precio Total: ${processed_data['monto_total']:,.0f} COP**"
            if processed_data.get('precio_detalle'):
                price_info += f"\n📊 {processed_data['precio_detalle']}"
        
        confirmation_msg = f"""{summary}{price_info}

❓ **¿Todos los datos son correctos?**

✅ **Responde "SÍ"** para confirmar y guardar la reserva
❌ **Responde "NO"** para corregir algún dato

¿Confirmas esta reserva? 😊"""
        
        # Move to confirmation step
        user_state["reserva_step"] = 2
        save_user_memory_func(user_id, memory)
        
        logger.info("Reserva procesada exitosamente, esperando confirmación", 
                   extra={"component": "conversation_service", "user_id": user_id})
        
        return confirmation_msg
        
    except Exception as e:
        logger.error(f"Error en process_reservation_step_1: {e}", 
                    extra={"component": "conversation_service", "user_id": user_id})
        
        return """❌ **Error procesando tu reserva**

Hubo un problema técnico al procesar tu información. 

🔄 **Por favor, intenta enviar tus datos nuevamente:**

📋 **Datos necesarios:**
• Correo electrónico y teléfono de contacto
• Cantidad de huéspedes y domo preferido  
• Fechas de entrada y salida
• Método de pago preferido

✏️ **Envía toda la información en un solo mensaje** 😊"""

def process_reservation_step_2(user_message: str, user_state: dict, memory, save_user_memory_func, 
                             user_id: str, db, Reserva, calcular_precio_reserva_func, 
                             save_reservation_to_pinecone_func) -> str:
    """Process reservation step 2 (confirmation) and return response with cancellation detection"""
    
    # 🚨 CANCELATION CHECK: Detectar cancelación antes de confirmar reserva
    if detect_cancellation_intent(user_message):
        handled, response = handle_cancellation_gracefully(
            user_message, user_state, memory, save_user_memory_func, user_id
        )
        return response
    
    try:
        logger.info("Procesando step 2 de reserva (confirmación)", 
                   extra={"component": "conversation_service", "user_id": user_id})
        
        message_clean = user_message.lower().strip()
        
        # Check for confirmation (YES)
        if message_clean in ["si", "sí", "yes", "confirmo", "confirmar", "conforme", "ok", "vale", "correcto"]:
            
            if not user_state.get("reserva_data"):
                # No reservation data found
                user_state["current_flow"] = "none"
                user_state["reserva_step"] = 0
                return """❌ **Error: No encontré datos de reserva**
                
🔄 **Por favor, inicia el proceso de reserva nuevamente:**
Envía "quiero hacer una reserva" para comenzar

¿Te ayudo con algo más? 😊"""
            
            reservation_data = user_state["reserva_data"]
            
            try:
                # Save reservation to database
                phone_clean = user_id.replace("whatsapp:", "") if user_id else ""
                
                # Handle date conversion safely
                if isinstance(reservation_data.get('fecha_entrada'), str):
                    fecha_entrada = datetime.fromisoformat(reservation_data['fecha_entrada']).date()
                else:
                    fecha_entrada = reservation_data['fecha_entrada']
                    
                if isinstance(reservation_data.get('fecha_salida'), str):
                    fecha_salida = datetime.fromisoformat(reservation_data['fecha_salida']).date()
                else:
                    fecha_salida = reservation_data['fecha_salida']
                
                # Create new reservation in database
                nueva_reserva = Reserva(
                    numero_whatsapp=phone_clean,
                    nombres_huespedes=reservation_data.get('nombres_huespedes', ''),
                    cantidad_huespedes=reservation_data['cantidad_huespedes'],
                    domo=reservation_data['domo'],
                    fecha_entrada=fecha_entrada,
                    fecha_salida=fecha_salida,
                    servicio_elegido=reservation_data.get('servicio_elegido', ''),
                    adicciones=reservation_data.get('servicios_adicionales', ''),
                    numero_contacto=reservation_data.get('numero_contacto', phone_clean),
                    email_contacto=reservation_data['email_contacto'],
                    metodo_pago=reservation_data.get('metodo_pago', 'Pendiente'),
                    monto_total=reservation_data.get('monto_total', 0.0),
                    comentarios_especiales=reservation_data.get('comentarios_especiales', '')
                )
                
                # Save to PostgreSQL database
                db.session.add(nueva_reserva)
                db.session.commit()
                
                logger.info(f"Reserva guardada exitosamente en PostgreSQL - ID: {nueva_reserva.id}", 
                           extra={"component": "conversation_service", "reservation_id": nueva_reserva.id})
                
                # Save to Pinecone (backup)
                pinecone_success = save_reservation_to_pinecone_func(phone_clean, reservation_data)
                
                # Generate success message
                success_msg = f"""🎉 **¡RESERVA CONFIRMADA Y GUARDADA!** ✅

📋 **Número de Reserva:** #{nueva_reserva.id}
👤 **Huésped(es):** {reservation_data.get('nombres_huespedes', 'N/A')}
🏠 **Domo:** {reservation_data['domo']}
👥 **Cantidad:** {reservation_data['cantidad_huespedes']} personas
📅 **Entrada:** {fecha_entrada.strftime('%d/%m/%Y')}
📅 **Salida:** {fecha_salida.strftime('%d/%m/%Y')}
💰 **Total:** ${reservation_data.get('monto_total', 0):,.0f} COP
💳 **Pago:** {reservation_data.get('metodo_pago', 'Pendiente')}

✅ **Tu reserva ha sido guardada en nuestra base de datos PostgreSQL**
📱 **Nos contactaremos contigo pronto para coordinar los detalles**

🌟 **¡Gracias por elegir Glamping Brillo de Luna!**

¿Hay algo más en lo que pueda ayudarte? 😊"""
                
                if not pinecone_success:
                    success_msg += "\n\n⚠️ *Nota: Tu reserva está segura en nuestra base de datos principal*"
                
                # Reset reservation flow
                user_state["current_flow"] = "none"
                user_state["reserva_step"] = 0
                user_state["reserva_data"] = {}
                save_user_memory_func(user_id, memory)
                
                return success_msg
                
            except Exception as db_error:
                # Rollback database transaction
                if db and hasattr(db, 'session'):
                    db.session.rollback()
                
                logger.error(f"Error guardando reserva en base de datos: {db_error}", 
                           extra={"component": "conversation_service", "user_id": user_id})
                
                # Reset reservation flow
                user_state["current_flow"] = "none"
                user_state["reserva_step"] = 0
                user_state["reserva_data"] = {}
                save_user_memory_func(user_id, memory)
                
                return """❌ **Error al guardar la reserva**

🔧 **Problema técnico temporal con la base de datos**

📞 **Por favor:**
• Guarda esta conversación como respaldo
• Contáctanos directamente por WhatsApp
• O intenta crear la reserva nuevamente

📋 **Tu información no se perdió y la procesaremos manualmente**

¿Te ayudo con algo más? 😊"""
        
        # Check for rejection/correction (NO)
        elif message_clean in ["no", "nop", "nope", "incorrecto", "mal", "error", "cambiar", "corregir", "modificar"]:
            
            # Return to data collection step
            user_state["reserva_step"] = 1
            save_user_memory_func(user_id, memory)
            
            return """🔧 **Perfecto, vamos a corregir los datos**

📋 **Envía nuevamente toda la información corregida:**

**DATOS OBLIGATORIOS:**
• **Correo electrónico** (ejemplo: maria@gmail.com)
• **Teléfono/WhatsApp** (ejemplo: 3001234567)  
• **Cantidad de huéspedes** (ejemplo: 2 personas)
• **Domo preferido** (Antares, Polaris, Sirius, Centaury)
• **Fecha entrada** (ejemplo: 15/12/2024)
• **Fecha salida** (ejemplo: 17/12/2024)
• **Método de pago** (efectivo, tarjeta, transferencia, Nequi)

**DATOS OPCIONALES:**
• Nombres completos de huéspedes
• Servicios adicionales
• Comentarios especiales

💡 **Ejemplo:**
"Reserva para Ana López, correo ana@email.com, teléfono 3009876543, 2 huéspedes, domo Polaris, entrada 20/12/2024, salida 22/12/2024, pago tarjeta"

✏️ **Envía todos los datos en un solo mensaje** 😊"""
        
        else:
            # Unclear response - ask for clarification
            return """❓ **No entendí tu respuesta**

Por favor responde claramente:

✅ **"SÍ"** - Para confirmar y guardar la reserva
❌ **"NO"** - Para corregir algún dato

¿Confirmas la reserva o quieres corregir algo? 😊"""
        
    except Exception as e:
        logger.error(f"Error en process_reservation_step_2: {e}", 
                    extra={"component": "conversation_service", "user_id": user_id})
        
        # Reset reservation flow on error
        user_state["current_flow"] = "none"
        user_state["reserva_step"] = 0
        user_state["reserva_data"] = {}
        save_user_memory_func(user_id, memory)
        
        return """❌ **Error procesando tu confirmación**

🔄 **Por favor, inicia el proceso de reserva nuevamente:**
Envía "quiero hacer una reserva" para comenzar

¿Te ayudo con algo más? 😊"""

def reset_user_state_on_error(user_state: dict, user_id: str):
    """Resetea el estado del usuario cuando hay errores críticos"""
    logger.warning(f"Reseteando estado del usuario {user_id} debido a error", 
                   extra={"component": "conversation_service", "user_id": user_id})
    user_state["current_flow"] = "none"
    user_state["reserva_step"] = 0
    user_state["reserva_data"] = {}
    user_state["waiting_for_availability"] = False
    user_state["waiting_for_domos_followup"] = False
    user_state["waiting_for_servicios_followup"] = False
    user_state["waiting_for_rag_followup"] = False
    user_state["waiting_for_domos_specific"] = False
    user_state["waiting_for_servicios_specific"] = False
    user_state["waiting_for_informacion_suboption"] = False
    user_state["waiting_for_politicas_suboption"] = False

def handle_website_link_request(user_message: str, validation_service) -> Tuple[bool, str]:
    """
    Detecta y maneja solicitudes de links de la página web según triggers específicos
    Variable 1: Link solo cuando el huésped pida fotos, imágenes, saber cómo son los domos/glamping,
    solicite la página web o pida reseñas/comentarios/calificaciones
    
    Args:
        user_message: Mensaje del usuario
        validation_service: Servicio de validación con detección de links
        
    Returns:
        Tuple[bool, str]: (handled, response_message)
    """
    try:
        if not validation_service:
            return False, ""
        
        # Detectar si debe compartir link según triggers específicos
        should_share, trigger_type, reason = validation_service.detect_website_link_request(user_message)
        
        if should_share:
            logger.info(f"Solicitud de link detectada y manejada: {trigger_type}", 
                       extra={"component": "conversation_service", "website_trigger": trigger_type})
            
            # Importar el servicio especializado para generar respuesta
            from services.website_link_service import get_website_link_service
            website_service = get_website_link_service()
            
            # Generar respuesta apropiada según el tipo de trigger
            response = website_service.generate_website_response(trigger_type, user_message)
            
            return True, response
        
        return False, ""
        
    except Exception as e:
        logger.error(f"Error manejando solicitud de link: {e}", 
                    extra={"component": "conversation_service"})
        return False, ""

def handle_admin_contact_request(user_message: str, validation_service) -> Tuple[bool, str, str]:
    """
    Detecta y maneja solicitudes de contacto de administradores según triggers de PQRS
    Variable 2: Contactos solo cuando se solicite información de contacto o se quiera hacer PQRS
    
    Args:
        user_message: Mensaje del usuario
        validation_service: Servicio de validación con detección de contactos admin
        
    Returns:
        Tuple[bool, str, str]: (handled, trigger_type, response_message)
    """
    try:
        if not validation_service:
            return False, "", ""
        
        # Detectar si debe compartir contacto según triggers específicos
        should_share, trigger_type, reason = validation_service.detect_admin_contact_request(user_message)
        
        if should_share:
            logger.info(f"Solicitud de contacto admin detectada y manejada: {trigger_type}", 
                       extra={"component": "conversation_service", "admin_trigger": trigger_type})
            
            # Importar el servicio especializado para generar respuesta
            from services.admin_contact_service import get_admin_contact_service
            admin_service = get_admin_contact_service()
            
            # Generar respuesta apropiada según el tipo de trigger
            response = admin_service.generate_admin_contact_response(trigger_type, user_message)
            
            return True, trigger_type, response
        
        return False, "", ""
        
    except Exception as e:
        logger.error(f"Error manejando solicitud de contacto admin: {e}", 
                    extra={"component": "conversation_service"})
        return False, "", ""

def handle_reservation_intent_v3(user_message: str, validation_service, qa_chains=None) -> Tuple[bool, str]:
    """
    Maneja intenciones de reserva según Variable 3 - Flujo inteligente
    Solo inicia flujo con "quiero hacer una reserva" o variantes específicas
    Si solo dice "reservas", pregunta si quiere hacer una o necesita información
    
    Args:
        user_message: Mensaje del usuario
        validation_service: Servicio de validación con análisis de intenciones
        qa_chains: Chains RAG para información de requisitos (opcional)
        
    Returns:
        Tuple[bool, str]: (handled, response_message)
    """
    try:
        if not validation_service:
            return False, ""
        
        # Analizar intención de reserva según Variable 3
        intent_type, action, reason = validation_service.analyze_reservation_intent_v3(user_message)
        
        if intent_type == "none":
            return False, ""
        
        logger.info(f"Intención de reserva manejada: {intent_type} -> {action}", 
                   extra={"component": "conversation_service", "reservation_intent": intent_type})
        
        # Importar el servicio especializado para generar respuestas
        from services.reservation_intent_service import get_reservation_intent_service
        reservation_service = get_reservation_intent_service()
        
        if action == "ask_clarification":
            # Usuario dijo solo "reservas" - pedir clarificación
            response = reservation_service.generate_clarification_response(user_message)
            return True, response
            
        elif action == "provide_info":
            # Usuario quiere información sobre reservas - usar RAG
            if qa_chains and "requisitos_reserva" in qa_chains:
                try:
                    rag_response = qa_chains["requisitos_reserva"].run(user_message)
                    return True, rag_response
                except Exception as e:
                    logger.error(f"Error usando RAG requisitos_reserva: {e}", 
                                extra={"component": "conversation_service"})
            
            # Fallback si no hay RAG disponible
            fallback_response = """📋 **INFORMACIÓN SOBRE RESERVAS**

📝 **Requisitos para reservar:**
• Nombre completo del huésped principal
• Número de contacto (WhatsApp preferido)
• Email de contacto
• Fechas de entrada y salida
• Número de huéspedes
• Selección de domo

💳 **Métodos de pago aceptados:**
• Efectivo
• Tarjeta de crédito/débito
• Transferencia bancaria
• Nequi/Daviplata

📞 **Para más información sobre políticas:**
• WhatsApp: +57 3054614926
• Email: glampingbrillodelunaguatavita@gmail.com

¿Necesitas ayuda con algún aspecto específico de las reservas? 😊"""
            
            return True, fallback_response
            
        elif action == "check_status":
            # Usuario quiere consultar estado de reserva existente
            response = reservation_service.generate_status_check_response(user_message)
            return True, response
            
        elif action == "start_flow":
            # Usuario quiere hacer una reserva - esto debe manejarse en el flujo principal
            # Retornamos False para que el flujo principal maneje el inicio de reserva
            return False, ""
        
        return False, ""
        
    except Exception as e:
        logger.error(f"Error manejando intención de reserva: {e}", 
                    extra={"component": "conversation_service"})
        return False, ""

def handle_comprehensive_fallback(user_message: str, validation_service, qa_chains: dict = None, user_state: dict = None) -> tuple[bool, str]:
    """
    Comprehensive fallback system to handle common requests without using AI agent
    This prevents OpenAI quota exhaustion issues by providing direct responses
    
    Args:
        user_message: User's message
        validation_service: Validation service instance
        qa_chains: Available QA chains for information retrieval
        user_state: Current user state
        
    Returns:
        tuple[bool, str]: (handled, response) - True if handled, with appropriate response
    """
    try:
        message_clean = user_message.lower().strip()
        logger.info(f"Checking comprehensive fallback for: '{message_clean[:50]}...'", 
                   extra={"component": "conversation_service", "phase": "fallback"})
        
        # Reset user state if they seem stuck
        if user_state and user_state.get("current_flow") in ["availability", "domos_followup", "servicios_followup"]:
            user_state["current_flow"] = "none"
            user_state["waiting_for_availability"] = False
            user_state["waiting_for_domos_followup"] = False
            user_state["waiting_for_servicios_followup"] = False
            user_state["waiting_for_rag_followup"] = False
            logger.info("Reset stuck user state", extra={"component": "conversation_service"})
        
        # Handle common menu-related requests
        if any(word in message_clean for word in ['menu', 'menú', 'opciones', 'ayuda', 'help']):
            return True, get_comprehensive_menu()
        
        # Handle domos requests
        if any(word in message_clean for word in ['domos', 'domo', 'alojamiento', 'habitacion', 'habitación']):
            return True, get_domos_information(qa_chains)
        
        # Handle servicios/actividades requests
        if any(word in message_clean for word in ['servicios', 'actividades', 'incluye', 'ofertas', 'experiencias']):
            return True, get_servicios_information(qa_chains)
        
        # Handle disponibilidad requests
        if any(word in message_clean for word in ['disponibilidad', 'disponible', 'fechas', 'calendario']):
            return True, get_disponibilidad_information()
        
        # Handle informacion requests
        if any(word in message_clean for word in ['informacion', 'información', 'ubicacion', 'ubicación', 'direccion', 'dirección']):
            return True, get_informacion_general(qa_chains)
        
        # Handle precios requests
        if any(word in message_clean for word in ['precio', 'precios', 'costo', 'costos', 'tarifa', 'tarifas']):
            return True, get_precios_information(qa_chains)
        
        # Handle reserva requests (should be caught by previous handlers but just in case)
        if any(word in message_clean for word in ['reserva', 'reservar', 'booking']):
            return True, get_reserva_information()
        
        # Handle fotos/imagenes requests
        if any(word in message_clean for word in ['fotos', 'foto', 'imagen', 'imagenes', 'imágenes', 'galeria', 'galería']):
            return True, get_imagenes_information()
        
        # Handle politicas requests
        if any(word in message_clean for word in ['politicas', 'políticas', 'normas', 'reglas', 'cancelacion', 'cancelación']):
            return True, get_politicas_information(qa_chains)
        
        # Handle contacto requests
        if any(word in message_clean for word in ['contacto', 'telefono', 'teléfono', 'whatsapp', 'email']):
            return True, get_contacto_information()
        
        return False, ""
        
    except Exception as e:
        logger.error(f"Error in comprehensive fallback: {e}", 
                    extra={"component": "conversation_service"})
        return False, ""

def get_comprehensive_menu() -> str:
    """Return comprehensive menu when requested"""
    return """🏕️ **¡BIENVENIDO A GLAMPING BRILLO DE LUNA!** 🌙✨

¡Hola! 👋 Mi nombre es *María* y soy tu asistente virtual especializada.

*Selecciona una opción escribiendo el número o palabra:*

1️⃣ **DOMOS** - "domos" - Información y precios de alojamiento
2️⃣ **SERVICIOS** - "servicios" - Todo lo que ofrecemos  
3️⃣ **DISPONIBILIDAD** - "disponibilidad" - Fechas y reservas
4️⃣ **INFORMACIÓN GENERAL** - "información" - Ubicación y políticas
5️⃣ **ACTIVIDADES** - "actividades" - Experiencias adicionales
6️⃣ **POLÍTICAS** - "políticas" - Normas y cancelaciones  
7️⃣ **IMÁGENES** - "fotos" - Galería de fotos
8️⃣ **ACCESIBILIDAD** - "accesibilidad" - Facilidades especiales

💬 **También puedes preguntar directamente:**
• "¿Cuánto cuesta?" - Precios
• "¿Está disponible el 15 de marzo?" - Fechas específicas
• "Quiero hacer una reserva" - Proceso de reserva
• "¿Dónde están ubicados?" - Información de ubicación

¿En qué te puedo ayudar? 😊"""

def get_domos_information(qa_chains: dict = None) -> str:
    """Return domos information using fallbacks"""
    try:
        domos_info = """
🏠 **NUESTROS DOMOS TEMÁTICOS:**

🌟 **DOMO ANTARES** (2 personas) - $650.000/noche
• Jacuzzi privado y malla catamarán
• Vista panorámica a represa de Tominé  
• Terraza con parasol
• Dos pisos: sala y cama principal

⭐ **DOMO POLARIS** (2-4 personas) - $550.000/noche
• Sofá cama para personas adicionales (+$100.000/persona extra)
• Vista maravillosa a la represa
• Cocineta completamente equipada
• Dos pisos con sala y dormitorio

🌌 **DOMO SIRIUS** (2 personas) - $450.000/noche
• Un solo piso diseño para parejas
• Vista bella a represa y montaña
• Terraza acogedora
• Nevera y cafetera incluidos

✨ **DOMO CENTAURY** (2 personas) - $450.000/noche
• Similar a Sirius, un solo piso
• Vista hermosa a represa y montaña
• Terraza relajante
• Nevera y cafetera incluidos

✨ **INCLUYE:**
• Desayuno gourmet continental
• Acceso a todas las instalaciones
• Wifi de alta velocidad
• Parqueadero privado
• Kit de bienvenida"""
        
        # Try to get enhanced information from RAG if available
        if qa_chains and "domos_info" in qa_chains and qa_chains["domos_info"]:
            try:
                rag_response = qa_chains["domos_info"].run(
                    "Información completa sobre los domos: tipos, características, precios y servicios incluidos"
                )
                if rag_response and len(rag_response) > 50:
                    domos_info = rag_response
            except Exception as e:
                logger.warning(f"RAG domos_info failed, using fallback: {e}")
        
        return f"""🏠 **INFORMACIÓN DE NUESTROS DOMOS** 🌟

{domos_info}

💡 **Opciones disponibles:**
• Escribe "disponibilidad" para consultar fechas
• Escribe "reservar" para hacer una reserva
• Escribe "fotos" para ver imágenes
• Pregúntame sobre un domo específico (Antares, Polaris, etc.)

¿Qué más te gustaría saber? 😊"""
        
    except Exception as e:
        logger.error(f"Error getting domos information: {e}")
        return "🏠 **DOMOS DISPONIBLES** 🌟\n\nTenemos 4 domos geodésicos únicos. Escribe 'menu' para ver todas las opciones o 'disponibilidad' para consultar fechas específicas."

def get_servicios_information(qa_chains: dict = None) -> str:
    """Return servicios information using fallbacks"""
    servicios_info = """
🛎️ **SERVICIOS INCLUIDOS:**
• Desayuno continental gourmet
• WiFi de alta velocidad gratuito  
• Parqueadero privado y seguro
• Acceso a instalaciones (zona de fogatas, senderos)
• Amenities de baño de lujo
• Recepción 24 horas

🎯 **ACTIVIDADES ADICIONALES:**
• Caminatas ecológicas guiadas - $25.000/persona
• Masajes terapéuticos - $80.000/sesión
• Cena romántica bajo estrellas - $120.000/pareja
• Observación de aves - $20.000/persona
• Tours nocturnos de estrellas - $30.000/persona
• Jacuzzi privado (según domo)
• Aromaterapia nocturna - $25.000/noche"""
    
    return f"""🛎️ **NUESTROS SERVICIOS** ✨

{servicios_info}

💡 **Opciones disponibles:**
• Escribe "precios" para ver tarifas completas
• Escribe "reservar" para incluir servicios en tu estadía
• Pregúntame sobre actividades específicas

¿Qué servicio te llama más la atención? 😊"""

def get_disponibilidad_information() -> str:
    """Return availability consultation information"""
    return """📅 **CONSULTA DE DISPONIBILIDAD** 📋

Para consultar disponibilidad necesito algunos datos:

📍 **¿Para qué fechas?**
   • Fecha de llegada (ej: 15 de septiembre)
   • Fecha de salida (ej: 17 de septiembre)

👥 **¿Cuántas personas?**
   • Número total de huéspedes

🏠 **¿Tipo de domo?** (opcional)
   • Antares, Polaris, Sirius, Centaury, o cualquiera disponible

💬 **Ejemplo:** "Disponibilidad para 2 personas del 15 al 17 de septiembre"

¿Cuáles son tus fechas? 📅"""

def get_informacion_general(qa_chains: dict = None) -> str:
    """Return general information"""
    return """ℹ️ **INFORMACIÓN GENERAL** 🌟

¿Qué información específica te gustaría conocer?

📍 **UBICACIÓN** - Dónde nos encontramos y cómo llegar
🏕️ **CONCEPTO** - Nuestra filosofía y sitio web
📋 **POLÍTICAS** - Normas, mascotas, cancelaciones
📞 **CONTACTO** - Teléfonos y emails directos

💬 **Escribe lo que te interesa:**
• "ubicación" para direcciones
• "concepto" para conocer sobre nosotros
• "políticas" para revisar normas
• "contacto" para información de contacto

¿Qué te interesa saber? 😊"""

def get_precios_information(qa_chains: dict = None) -> str:
    """Return pricing information"""
    return """💰 **PRECIOS DOMOS 2024** 💳

🌟 **DOMO ANTARES**: $650.000 COP/noche para pareja
⭐ **DOMO POLARIS**: $550.000 COP/noche para pareja (+$100.000 por persona adicional)
🌌 **DOMO SIRIUS**: $450.000 COP/noche para pareja  
✨ **DOMO CENTAURY**: $450.000 COP/noche para pareja

✨ **INCLUYE:**
• Desayuno gourmet continental
• WiFi, parqueadero, instalaciones
• Kit de bienvenida

🎯 **SERVICIOS ADICIONALES:**
• Masajes: $80.000/sesión
• Cena romántica: $120.000/pareja
• Actividades desde: $20.000/persona

📅 **Para consultar disponibilidad:**
• Escribe "disponibilidad" con tu fecha preferida
Escribe "disponibilidad" y te ayudo 😊"""

def get_reserva_information() -> str:
    """Return reservation process information"""
    return """📝 **PROCESO DE RESERVA** ✨

Para hacer tu reserva necesito:

✅ **Información personal:**
• Nombres completos de huéspedes
• Teléfono y email de contacto

✅ **Detalles de estadía:**
• Fechas de entrada y salida
• Domo preferido
• Número de personas
• Servicios adicionales deseados

💳 **Métodos de pago:**
• Transferencia bancaria
• Efectivo
• Tarjeta de crédito/débito

📞 **Para reservar:**
• Escribe "quiero hacer una reserva"
• O dame las fechas que te interesan

¡Estoy lista para ayudarte! 😊"""

def get_imagenes_information() -> str:
    """Return images/gallery information"""
    return """📸 **GALERÍA DE IMÁGENES** 🌟

Puedes ver todas las fotos en:

🌐 **Sitio Web:** https://glampingbrillodelaluna.com
📱 **Instagram:** @glampingbrillodelaluna  
📘 **Facebook:** Glamping Brillo de Luna

🏠 **¿Qué puedes ver?**
• Todos nuestros domos geodésicos
• Vistas panorámicas del entorno
• Instalaciones y servicios
• Experiencias de huéspedes

📸 **También disponible:**
• Tours virtuales 360°
• Videos de experiencias
• Galería actualizada semanalmente

¿Algún domo en particular te llamó la atención? 😊"""

def get_politicas_information(qa_chains: dict = None) -> str:
    """Return policies information"""
    return """📋 **POLÍTICAS PRINCIPALES** 📄

📅 **RESERVAS Y CANCELACIONES:**
• Check-in: 3:00 PM | Check-out: 12:00 PM
• Cancelación gratuita hasta 48 horas antes
• Modificaciones sin costo (sujeto a disponibilidad)

🐕 **POLÍTICAS DE MASCOTAS:**
• Se permiten bajo condiciones específicas
• Tarifa adicional: $20.000/mascota/noche
• Certificado de vacunación requerido

🚫 **NORMAS GENERALES:**
• No fumar en domos
• Silencio después de 10:00 PM
• Respetar capacidad máxima

📞 **¿Necesitas detalles específicos?**
• Escribe "mascotas" para políticas de animales
• Escribe "cancelación" para términos específicos

¿Hay alguna política que te interese? 😊"""

def get_contacto_information() -> str:
    """Return contact information"""
    return """📞 **INFORMACIÓN DE CONTACTO** 📱

🏕️ **GLAMPING BRILLO DE LUNA**

📱 **WhatsApp:** +57 305 461 4926
📧 **Email:** glampingbrillodelunaguatavita@gmail.com
🌐 **Web:** https://glampingbrillodelaluna.com

🕐 **Horario de atención:**
Lunes a Domingo: 8:00 AM - 9:00 PM

📍 **Ubicación:** Guatavita, Cundinamarca

💬 **¿En qué más puedo ayudarte?**
• Escribe "ubicación" para direcciones específicas
• Escribe "reservar" para hacer una reserva
• Pregúntame lo que necesites

¡Estamos aquí para ayudarte! 🌟"""

def process_simple_response_with_prompt(error_prompt: str, user_message: str) -> str:
    """
    Procesa un prompt de error usando un método simple sin el agente completo
    para evitar errores adicionales durante el manejo de errores
    """
    try:
        from services.llm_service import get_llm_service
        
        # Usar LLM Service directamente sin el agente completo
        llm_service = get_llm_service()
        
        # Crear un prompt simple y directo
        simple_prompt = f"""{error_prompt}

Usuario consulta: {user_message}

Responde de manera clara, útil y empática como el asistente de Glamping Brillo de Luna."""
        
        # Usar el LLM directamente para una respuesta simple
        try:
            response = llm_service.generate_simple_response(simple_prompt)
            if response and len(response.strip()) > 10:
                return response.strip()
        except Exception as llm_error:
            logger.error(f"Error usando LLM simple para error recovery: {llm_error}")
        
        # Fallback: usar el prompt como base para una respuesta templática
        if "api_limit" in error_prompt.lower() or "límite" in error_prompt.lower():
            return """🙏 Disculpa, estoy experimentando un alto volumen de consultas.

🏕️ **Mientras tanto, puedes:**
• Contactarnos directamente: +57 305 461 4926
• Visitar nuestra web: https://glampingbrillodelaluna.com
• Escribir tu consulta específica y te responderé en unos minutos

¡Gracias por tu paciencia! 🌟"""
        
        elif "timeout" in error_prompt.lower() or "tiempo" in error_prompt.lower():
            return """⏱️ La consulta está tomando más tiempo del esperado.

💡 **Intenta reformular tu pregunta de manera más específica:**
• ¿Qué información necesitas sobre los domos?
• Escribe "precios" o "disponibilidad" para más información
• ¿Necesitas ayuda con una reserva?

🌟 ¡Estoy aquí para ayudarte!"""
        
        elif "validation" in error_prompt.lower() or "validación" in error_prompt.lower():
            return """📝 Hubo un problema procesando tu solicitud.

🔄 **Por favor, intenta nuevamente con:**
• Información más específica
• Fechas en formato DD/MM/AAAA
• Detalles claros sobre lo que necesitas

💬 ¿En qué puedo ayudarte específicamente?"""
        
        else:
            # NUEVO: Intentar fallback específico antes de respuesta genérica
            try:
                from services.fallback_service import detect_topic_and_provide_fallback
                handled, fallback_response, topic = detect_topic_and_provide_fallback(user_message)

                if handled and fallback_response:
                    logger.info(f"Fallback topic used in process_simple_response_with_prompt: {topic}")
                    return fallback_response
            except Exception as fallback_error:
                logger.warning(f"Fallback failed in process_simple_response_with_prompt: {fallback_error}")

            # General error template (fallback final)
            return """🛠️ Tuve un inconveniente técnico temporal.

🏕️ **Glamping Brillo de Luna está aquí para ti:**
📱 WhatsApp: +57 305 461 4926
📧 Email: glampingbrillodelunaguatavita@gmail.com

💫 ¿Podrías reformular tu pregunta? ¡Te ayudo enseguida!"""
    
    except Exception as e:
        logger.error(f"Error en process_simple_response_with_prompt: {e}")
        return """🙏 Disculpa, tuve un inconveniente.

🏠 **Contacta directamente:**
📱 +57 305 461 4926
📧 glampingbrillodelunaguatavita@gmail.com

🌟 ¡Estaremos encantados de ayudarte!"""

def process_ai_agent(user_message: str, memory, tools, initialize_agent_safe_func, 
                    run_agent_safe_func, save_user_memory_func, user_id: str, user_state: dict = None) -> str:
    """Process message through AI agent and return response"""
    try:
        # Initialize agent with robust handling
        init_success, custom_agent, init_error = initialize_agent_safe_func(tools, memory, max_retries=3)
        
        if not init_success:
            logger.error(f"Error al inicializar agente: {init_error}", extra={"phase": "conversation", "component": "agent_init"})
            if user_state:
                reset_user_state_on_error(user_state, user_id)
            return """🔧 **Problema técnico temporal**

😊 **¡Pero estoy aquí para ayudarte!**

🏕️ Puedes preguntarme sobre:
• **Domos** - Información y precios  
• **Servicios** - Lo que incluye tu estadía
• **Disponibilidad** - Fechas libres y reservas
• **Reservar** - Proceso de reserva directo

💬 **¿En qué puedo ayudarte?** 🌟"""
        else:
            # Execute agent with robust handling
            run_success, result, run_error = run_agent_safe_func(custom_agent, user_message, user_id)
            
            if run_success:
                agent_answer = result
            else:
                logger.error(f"Error ejecutando agente: {run_error}", extra={"phase": "conversation", "component": "agent_run"})
                
                # Reset state on critical errors
                if user_state and ("max_retries" in run_error.lower() or "unexpected" in run_error.lower()):
                    reset_user_state_on_error(user_state, user_id)
                
                # Intelligent fallback using PromptService for dynamic error handling
                try:
                    from services.prompt_service import get_prompt_service
                    prompt_service = get_prompt_service()
                    
                    # NUEVO: MANEJAR ESTADO DE CONVERSACIÓN ANTES DE RESETEAR
                    if user_state and ("rate limit" in run_error.lower() or "quota" in run_error.lower() or "429" in run_error):
                        # Si está esperando sub-opción de información general, procesarla directamente
                        if (user_state.get("waiting_for_informacion_suboption") and
                            user_state.get("current_flow") == "informacion_general"):
                            try:
                                from services.menu_service import create_menu_service
                                menu_service = create_menu_service({}, None)  # qa_chains y validation_service pueden ser None para fallback
                                response = menu_service.handle_informacion_general_suboptions(user_message, user_state)

                                logger.info(f"Information suboption processed during 429 error in conversation_service: {user_message[:30]}",
                                           extra={"user_id": user_id, "flow": "informacion_general"})
                                return response

                            except Exception as suboption_error:
                                logger.error(f"Error procesando sub-opción durante 429 en conversation_service: {suboption_error}")
                                # Continuar con lógica de reset si falla

                        # Solo resetear estado si NO pudimos procesar la sub-opción
                        reset_user_state_on_error(user_state, user_id)
                    
                    # Generate dynamic error responses using PromptService
                    if "rate limit" in run_error.lower() or "quota" in run_error.lower() or "429" in run_error:
                        error_prompt = prompt_service.get_error_recovery_prompt("api_limit", user_message)
                        
                        # Try to detect if this could be a recommendation request and handle differently
                        try:
                            from services.recommendation_service import create_recommendation_service
                            rec_service = create_recommendation_service({})
                            
                            if rec_service.detect_recommendation_intent(user_message):
                                # Generate template-based recommendation instead of generic response
                                agent_answer = generate_template_recommendation(user_message, {})
                            else:
                                # Use PromptService for intelligent API limit response
                                agent_answer = process_simple_response_with_prompt(error_prompt, user_message)
                        except Exception:
                            # Fallback if recommendation service fails
                            agent_answer = process_simple_response_with_prompt(error_prompt, user_message)
                            
                    elif "timeout" in run_error.lower():
                        error_prompt = prompt_service.get_error_recovery_prompt("timeout", user_message)
                        agent_answer = process_simple_response_with_prompt(error_prompt, user_message)
                        
                    elif "parsing" in run_error.lower():
                        error_prompt = prompt_service.get_error_recovery_prompt("validation_error", user_message)
                        agent_answer = process_simple_response_with_prompt(error_prompt, user_message)
                        
                    elif "max_retries" in run_error.lower() or "unexpected" in run_error.lower():
                        error_prompt = prompt_service.get_error_recovery_prompt("tool_error", user_message)
                        agent_answer = process_simple_response_with_prompt(error_prompt, user_message)
                        
                    else:
                        # General error - use default error recovery
                        error_prompt = prompt_service.get_error_recovery_prompt("general", user_message)
                        agent_answer = process_simple_response_with_prompt(error_prompt, user_message)
                        
                except Exception as prompt_error:
                    logger.error(f"Error usando PromptService para recovery: {prompt_error}")
                    
                    # Final fallback with basic error response
                    agent_answer = """🙏 Disculpa, tuve un inconveniente técnico.

🏠 **Glamping Brillo de Luna** está aquí para ayudarte:

💬 **Contáctanos directamente:**
📱 WhatsApp: +57 305 461 4926
📧 Email: glampingbrillodelunaguatavita@gmail.com

🌟 ¿En qué más puedo ayudarte sobre nuestro glamping?"""
        
        # Save memory regardless of result
        save_user_memory_func(user_id, memory)
        
        # Handle special reservation flow trigger
        if agent_answer == "REQUEST_RESERVATION_DETAILS":
            return (
                "¡Claro! Para tu reserva, necesito los siguientes datos:\n"
                "- Tu nombre completo y el de tus acompañantes\n"
                "- Tipo de domo que te gustaría reservar\n"
                "- Fecha de entrada y fecha de salida (Formato DD/MM/AAAA)\n"
                "- Servicios adicionales que quieras incluir (ej. cena romántica, masajes)\n"
                "- Cualquier adición especial (ej. mascota, decoración específica)\n"
                "- Tu número de teléfono de contacto\n"
                "- Tu correo electrónico de contacto\n"
                "- Método de pago preferido (efectivo, transferencia, tarjeta)\n"
                "- Comentarios especiales u observaciones adicionales\n\n"
                "Por favor, envíame toda esta información en un solo mensaje para procesar tu solicitud."
            )
        
        # Replace generic menu responses with specific ones
        agent_answer = replace_generic_menu_response(agent_answer, user_message)
        
        # 🔄 NUEVO: Detectar si la respuesta del agente puede generar seguimiento
        if user_state:
            context_info = detect_rag_response_pattern(agent_answer)
            update_conversation_context(user_state, context_info)
            
            if context_info.get("has_followup_potential"):
                logger.info(f"Set RAG followup context: {context_info.get('topic')} with entities: {context_info.get('entities')}", 
                           extra={"component": "conversation_service", "user_id": user_id})
        
        return agent_answer
        
    except Exception as e:
        logger.error(f"Error inesperado en procesamiento conversacional: {e}", extra={"phase": "conversation", "component": "general"})
        if user_state:
            reset_user_state_on_error(user_state, user_id)
        return """🔧 **Error inesperado - Reiniciando**

😊 **¡Empecemos de nuevo!**

🏕️ Puedes preguntarme sobre:
• **Domos** - Información y precios
• **Servicios** - Lo que incluye tu estadía
• **Disponibilidad** - Fechas libres y reservas  
• **Reservar** - Proceso de reserva directo

💬 **¿En qué puedo ayudarte?** 🌟"""

def messages_to_dict(messages):
    """Convert LangChain messages to dictionary format for JSON response"""
    try:
        result = []
        for msg in messages:
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                result.append({
                    "type": msg.type,
                    "content": msg.content
                })
            elif hasattr(msg, 'content'):
                # Fallback for different message types
                msg_type = "human" if "human" in str(type(msg)).lower() else "ai"
                result.append({
                    "type": msg_type,
                    "content": msg.content
                })
        return result
    except Exception as e:
        logger.warning(f"Error converting messages to dict: {e}", extra={"phase": "conversation", "component": "message_conversion"})
        return []

def process_chat_conversation(user_input: str, session_id: str, user_memories: dict, user_states: dict,
                            load_user_memory_func, save_user_memory_func, is_greeting_message_func,
                            get_welcome_menu_func, is_menu_selection_func, handle_menu_selection_func,
                            handle_availability_request_func, parse_reservation_details_func,
                            validate_and_process_reservation_data_func, calcular_precio_reserva_func,
                            db, Reserva, save_reservation_to_pinecone_func, tools, 
                            initialize_agent_safe_func, run_agent_safe_func, qa_chains) -> dict:
    """
    Process chat conversation and return JSON response
    This function handles the /chat endpoint logic using the unified conversation service
    """
    
    # Initialize user memory and state
    if session_id not in user_memories:
        user_memories[session_id] = load_user_memory_func(session_id)
    if session_id not in user_states:
        user_states[session_id] = {
            "current_flow": "none", 
            "reserva_step": 0, 
            "reserva_data": {}, 
            "waiting_for_availability": False,
            "previous_context": "",  # NUEVO
            "last_action": "",       # NUEVO
            "waiting_for_continuation": False  # NUEVO
        }
    
    memory = user_memories[session_id]
    user_state = user_states[session_id]
    response_output = "Lo siento, no pude procesar tu solicitud en este momento."

    # 🚨 PRIORIDAD MÁXIMA: Detectar cancelación ANTES que cualquier otro flujo
    # Esta es la implementación de máquina de estados robusta
    if detect_cancellation_intent(user_input):
        handled, response = handle_cancellation_gracefully(
            user_input, user_state, memory, save_user_memory_func, session_id
        )
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }

    # 1. Handle greeting in new conversation
    handled, response = handle_greeting_new_conversation(
        memory, user_input, is_greeting_message_func, get_welcome_menu_func, save_user_memory_func, session_id
    )
    if handled:
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }
    
    # 2. Handle continuation of flow with context service (NEW)
    from services.context_service import get_context_service
    context_service = get_context_service()
    
    if user_state.get("waiting_for_continuation", False):
        # Usar context_service para respuestas más inteligentes
        continuation_response = context_service.get_continuation_response(session_id, user_input)
        
        if continuation_response:
            user_state["waiting_for_continuation"] = False
            
            # Guardar contexto de la continuación
            context_service.remember_context(session_id, 'continuation_handled', {
                'user_input': user_input,
                'response_type': 'continuation'
            })
            
            add_message_to_memory(memory, user_input, continuation_response)
            save_user_memory_func(session_id, memory)
            return {
                "session_id": session_id,
                "response": continuation_response,
                "memory": messages_to_dict(memory.chat_memory.messages)
            }
        
        # Fallback al método original si context_service no maneja
        fallback_response = handle_continuation_response(
            user_input, user_state, user_state.get("previous_context", "")
        )
        if fallback_response:
            user_state["waiting_for_continuation"] = False
            add_message_to_memory(memory, user_input, fallback_response)
            save_user_memory_func(session_id, memory)
            return {
                "session_id": session_id,
                "response": fallback_response,
                "memory": messages_to_dict(memory.chat_memory.messages)
            }
    
    # 3. Handle RAG followup flow (NEW - for conversational context)
    logger.info(f"Checking RAG followup: user_state={user_state.get('current_flow')}, waiting={user_state.get('waiting_for_rag_followup')}", 
               extra={"component": "conversation_service"})
    handled, response = handle_rag_followup_unified(
        user_input, user_state, memory, initialize_agent_safe_func, run_agent_safe_func,
        save_user_memory_func, session_id
    )
    logger.info(f"RAG followup result: handled={handled}", 
               extra={"component": "conversation_service"})
    if handled:
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }

    # 3. Handle domos followup flow (before menu selection)
    logger.info(f"Checking domos followup: user_state={user_state}", 
               extra={"component": "conversation_service"})
    handled, response = handle_domos_followup_unified(
        user_input, user_state, memory, qa_chains, save_user_memory_func, session_id
    )
    logger.info(f"Domos followup result: handled={handled}", 
               extra={"component": "conversation_service"})
    if handled:
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }

    # 4. Handle servicios followup flow
    handled, response = handle_servicios_followup_unified(
        user_input, user_state, memory, qa_chains, save_user_memory_func, session_id
    )
    if handled:
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }

    # 4. Handle domos specific requests  
    handled, response = handle_domos_specific_unified(
        user_input, user_state, memory, qa_chains, save_user_memory_func, session_id
    )
    if handled:
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }

    # 5. Handle servicios specific requests
    handled, response = handle_servicios_specific_unified(
        user_input, user_state, memory, qa_chains, save_user_memory_func, session_id
    )
    if handled:
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }

    # 6. Handle menu selection (only when no active flow)
    if user_state.get("current_flow") == "none":
        logger.info("Attempting menu selection handling", extra={"component": "conversation_service"})
        handled, response = handle_menu_selection_unified(
            user_input, user_state, memory, qa_chains, handle_menu_selection_func, 
            save_user_memory_func, session_id, is_menu_selection_func
        )
        logger.info(f"Menu selection handled: {handled}", extra={"component": "conversation_service"})
        if handled:
            if isinstance(response, dict):
                response_text = response["message"]
            else:
                response_text = response
            
            # 🔄 CRÍTICO: Detectar si la respuesta del menú puede generar seguimiento
            response_text = process_response_and_detect_context(response_text, user_state, session_id)
            
            return {
                "session_id": session_id,
                "response": response_text,
                "memory": messages_to_dict(memory.chat_memory.messages)
            }
    else:
        logger.info(f"Skipping menu selection because current_flow={user_state.get('current_flow')}", 
                   extra={"component": "conversation_service"})

    # 7. Handle availability request (with enhanced workflow)
    handled, response = handle_availability_request_unified(
        user_input, user_state, memory, qa_chains, handle_availability_request_func, 
        save_user_memory_func, session_id
    )
    if handled:
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }
    # 8. Handle reservation flow initiation
    if user_state["current_flow"] == "none" and detect_reservation_intent(user_input):
        response = initiate_reservation_flow(user_state, memory, save_user_memory_func, session_id)
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }
    
    # 9. Process reservation step 1 (data collection)
    if user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 1:
        response = process_reservation_step_1(
            user_input, user_state, memory, save_user_memory_func, session_id,
            parse_reservation_details_func, validate_and_process_reservation_data_func, calcular_precio_reserva_func
        )
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }

    # 10. Process reservation step 2 (confirmation)
    if user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 2:
        response = process_reservation_step_2(
            user_input, user_state, memory, save_user_memory_func, session_id,
            db, Reserva, calcular_precio_reserva_func, save_reservation_to_pinecone_func
        )
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }

    # 11. Handle website link requests (Variable 1 implementation)
    # Note: validation_service needs to be passed as parameter
    # For now, this will be handled by the AI agent
    
    # 12. Handle admin contact requests (Variable 2 implementation)
    # Note: validation_service needs to be passed as parameter
    # For now, this will be handled by the AI agent
    
    # 13. Handle intelligent recommendations (NEW - LLM as business logic tool)
    # MOVED BEFORE AI AGENT to ensure recommendations are processed even with OpenAI quota issues
    handled, response = handle_intelligent_recommendations(
        user_input, user_state, memory, qa_chains, initialize_agent_safe_func, 
        run_agent_safe_func, save_user_memory_func, session_id
    )
    if handled:
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }
    
    # 14. ¿Es consulta específica? → ACTIVAR AGENTE IA CON CONTEXTO (NEW)
    # Usar context_service para decisiones inteligentes (ya importado arriba)
    user_context = context_service.get_user_context(session_id)
    
    # En el flujo principal:
    if context_service.should_activate_ai_agent(user_input, user_context):
        logger.info(f"Context service suggests AI agent activation for {session_id}")
        # Usar agente IA con contexto específico
        agent_answer = process_ai_agent(
            user_input, memory, tools, initialize_agent_safe_func, run_agent_safe_func, 
            save_user_memory_func, session_id, user_state
        )
        
        # Guardar contexto de la respuesta del agente
        context_service.remember_context(session_id, 'ai_agent_response', {
            'query': user_input,
            'response_preview': agent_answer[:100]
        })
        
        # 🔄 Detectar contexto también en respuestas del AI agent
        agent_answer = process_response_and_detect_context(agent_answer, user_state, session_id)
        
        return {
            "session_id": session_id,
            "response": agent_answer,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }
    
    # Si no es ningún flujo específico, activar el agente IA para consultas complejas (fallback)
    elif user_state["current_flow"] == "none":
        logger.info(f"Fallback AI agent activation for {session_id}")
        agent_answer = process_ai_agent(
            user_input, memory, tools, initialize_agent_safe_func, run_agent_safe_func, 
            save_user_memory_func, session_id, user_state
        )
        
        # 🔄 Detectar contexto también en respuestas del AI agent
        agent_answer = process_response_and_detect_context(agent_answer, user_state, session_id)
        
        return {
            "session_id": session_id,
            "response": agent_answer,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }

    # 15. Handle comprehensive fallback BEFORE AI agent to prevent quota exhaustion
    from services.validation_service import ValidationService
    validation_service = ValidationService()
    handled, response = handle_comprehensive_fallback(
        user_input, validation_service, qa_chains, user_state
    )
    if handled:
        add_message_to_memory(memory, user_input, response)
        save_user_memory_func(session_id, memory)
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }
    
    # 16. Process through AI agent (LAST RESORT - only if no other handler worked)
    agent_answer = process_ai_agent(
        user_input, memory, tools, initialize_agent_safe_func, run_agent_safe_func, 
        save_user_memory_func, session_id, user_state
    )
    
    # 🔄 Detectar contexto también en respuestas del AI agent (redundancia por seguridad)
    agent_answer = process_response_and_detect_context(agent_answer, user_state, session_id)
    
    return {
        "session_id": session_id,
        "response": agent_answer,
        "memory": messages_to_dict(memory.chat_memory.messages)
    }


def handle_domos_followup_unified(user_message: str, user_state: dict, memory, qa_chains,
                                save_user_memory_func, user_id: str, validation_service=None) -> Tuple[bool, str]:
    """Handle domos followup flow - returns (handled, response)"""
    if user_state.get("waiting_for_domos_followup") and user_state.get("current_flow") == "domos_followup":
        try:
            if validation_service:
                from services.menu_service import create_menu_service
                menu_service = create_menu_service(qa_chains, validation_service)
                response = menu_service.handle_domos_followup(user_message, user_state)
                
                add_message_to_memory(memory, user_message, response)
                save_user_memory_func(user_id, memory)
                return True, response
            else:
                # Fallback simple
                user_state["current_flow"] = "none"
                user_state["waiting_for_domos_followup"] = False
                response = "Claro, ¿en qué más puedo ayudarte?"
                add_message_to_memory(memory, user_message, response)
                save_user_memory_func(user_id, memory)
                return True, response
                
        except Exception as e:
            logger.error(f"Error en seguimiento de domos: {e}", 
                        extra={"component": "conversation_service", "user_id": user_id})
            user_state["current_flow"] = "none"
            user_state["waiting_for_domos_followup"] = False
            return True, "Tuve un problema procesando tu respuesta. ¿En qué más puedo ayudarte?"
    
    return False, ""


def handle_domos_specific_unified(user_message: str, user_state: dict, memory, qa_chains,
                                save_user_memory_func, user_id: str, validation_service=None) -> Tuple[bool, str]:
    """Handle domos specific requests - returns (handled, response)"""
    if user_state.get("waiting_for_domos_specific") and user_state.get("current_flow") == "domos_specific":
        try:
            if validation_service:
                from services.menu_service import create_menu_service
                menu_service = create_menu_service(qa_chains, validation_service)
                response = menu_service.handle_domos_specific_request(user_message, user_state)
                
                add_message_to_memory(memory, user_message, response)
                save_user_memory_func(user_id, memory)
                return True, response
            else:
                # Fallback simple
                user_state["current_flow"] = "none"
                user_state["waiting_for_domos_specific"] = False
                response = "Información específica sobre domos procesada. ¿En qué más puedo ayudarte?"
                add_message_to_memory(memory, user_message, response)
                save_user_memory_func(user_id, memory)
                return True, response
                
        except Exception as e:
            logger.error(f"Error en consulta específica de domos: {e}", 
                        extra={"component": "conversation_service", "user_id": user_id})
            user_state["current_flow"] = "none"
            user_state["waiting_for_domos_specific"] = False
            return True, "Tuve un problema procesando tu consulta. ¿Podrías reformular tu pregunta?"
    
    return False, ""


def handle_servicios_followup_unified(user_message: str, user_state: dict, memory, qa_chains,
                                    save_user_memory_func, user_id: str, validation_service=None) -> Tuple[bool, str]:
    """Handle servicios followup flow - returns (handled, response)"""
    if user_state.get("waiting_for_servicios_followup") and user_state.get("current_flow") == "servicios_followup":
        try:
            if validation_service:
                from services.menu_service import create_menu_service
                menu_service = create_menu_service(qa_chains, validation_service)
                response = menu_service.handle_servicios_followup(user_message, user_state)
                
                add_message_to_memory(memory, user_message, response)
                save_user_memory_func(user_id, memory)
                return True, response
            else:
                # Fallback simple
                user_state["current_flow"] = "none"
                user_state["waiting_for_servicios_followup"] = False
                response = "Claro, ¿en qué más puedo ayudarte?"
                add_message_to_memory(memory, user_message, response)
                save_user_memory_func(user_id, memory)
                return True, response
                
        except Exception as e:
            logger.error(f"Error en seguimiento de servicios: {e}", 
                        extra={"component": "conversation_service", "user_id": user_id})
            user_state["current_flow"] = "none"
            user_state["waiting_for_servicios_followup"] = False
            return True, "Tuve un problema procesando tu respuesta. ¿En qué más puedo ayudarte?"
    
    return False, ""


def handle_servicios_specific_unified(user_message: str, user_state: dict, memory, qa_chains,
                                    save_user_memory_func, user_id: str, validation_service=None) -> Tuple[bool, str]:
    """Handle servicios specific requests - returns (handled, response)"""
    if user_state.get("waiting_for_servicios_specific") and user_state.get("current_flow") == "servicios_specific":
        try:
            if validation_service:
                from services.menu_service import create_menu_service
                menu_service = create_menu_service(qa_chains, validation_service)
                response = menu_service.handle_servicios_specific_request(user_message, user_state)
                
                add_message_to_memory(memory, user_message, response)
                save_user_memory_func(user_id, memory)
                return True, response
            else:
                # Fallback simple
                user_state["current_flow"] = "none"
                user_state["waiting_for_servicios_specific"] = False
                response = "Información específica sobre servicios procesada. ¿En qué más puedo ayudarte?"
                add_message_to_memory(memory, user_message, response)
                save_user_memory_func(user_id, memory)
                return True, response
                
        except Exception as e:
            logger.error(f"Error en consulta específica de servicios: {e}", 
                        extra={"component": "conversation_service", "user_id": user_id})
            user_state["current_flow"] = "none"
            user_state["waiting_for_servicios_specific"] = False
            return True, "Tuve un problema procesando tu consulta. ¿Podrías reformular tu pregunta?"
    
    # Handle informacion general suboptions
    if (user_state.get("waiting_for_informacion_suboption") and 
        user_state.get("current_flow") == "informacion_general") or \
       (user_state.get("waiting_for_politicas_suboption") and 
        user_state.get("current_flow") == "politicas_submenu"):
        try:
            # Always try to use enhanced menu service, even without validation_service
            from services.menu_service import create_menu_service
            menu_service = create_menu_service(qa_chains, validation_service)
            response = menu_service.handle_informacion_general_suboptions(user_message, user_state)
            
            add_message_to_memory(memory, user_message, response)
            save_user_memory_func(user_id, memory)
            return True, response
        
        except Exception as e:
            logger.error(f"Error en sub-opciones de información general: {e}", 
                        extra={"component": "conversation_service", "user_id": user_id})
            user_state["current_flow"] = "none"
            user_state["waiting_for_informacion_suboption"] = False
            user_state["waiting_for_politicas_suboption"] = False
            return True, "Tuve un problema procesando tu solicitud de información. ¿Podrías intentar de nuevo?"
    
    return False, ""


def generate_template_recommendation(user_input: str, qa_chains: dict = None) -> str:
    """
    Genera recomendaciones inteligentes usando templates cuando el LLM no está disponible
    Analiza el contexto del mensaje para personalizar la respuesta
    """
    message_lower = user_input.lower()
    
    # Detectar contexto familiar/grupal
    is_family = any(word in message_lower for word in ["familia", "hijos", "niños", "niñas", "bebé", "bebés"])
    is_couple = any(word in message_lower for word in ["pareja", "novio", "novia", "esposo", "esposa", "aniversario", "romántico"])
    is_friends = any(word in message_lower for word in ["amigos", "amigas", "grupo", "amistades"])
    
    # Detectar tipo de experiencia deseada
    wants_relaxation = any(word in message_lower for word in ["descansar", "relajar", "tranquilo", "paz", "desconectar"])
    wants_adventure = any(word in message_lower for word in ["aventura", "emoción", "actividades", "deporte"])
    wants_nature = any(word in message_lower for word in ["naturaleza", "aire libre", "monte", "campo", "verde"])
    wants_romantic = any(word in message_lower for word in ["romántico", "romance", "luna de miel", "especial", "íntimo"])
    
    # Seleccionar recomendación base según contexto
    if is_family:
        base_recommendation = {
            "domo": "Polaris",
            "reason": "perfecto para familias con sofá cama adicional",
            "price": "$550.000/noche",
            "capacity": "2-4 personas",
            "special_features": ["Cocineta equipada", "Espacio amplio", "Vista segura para niños", "Dos pisos"]
        }
    elif is_couple and wants_romantic:
        base_recommendation = {
            "domo": "Antares", 
            "reason": "ideal para parejas con jacuzzi privado",
            "price": "$650.000/noche",
            "capacity": "2 personas",
            "special_features": ["Jacuzzi privado", "Vista panorámica", "Malla catamarán", "Ambiente íntimo"]
        }
    elif wants_relaxation or wants_nature:
        base_recommendation = {
            "domo": "Sirius o Centaury",
            "reason": "perfectos para desconectar en la naturaleza",
            "price": "$450.000/noche",
            "capacity": "2 personas",
            "special_features": ["Un piso acogedor", "Vista a represa y montaña", "Terraza tranquila", "Precio accesible"]
        }
    else:
        # Recomendación general balanceada
        base_recommendation = {
            "domo": "Polaris",
            "reason": "nuestra opción más versátil",
            "price": "$550.000/noche", 
            "capacity": "2-4 personas",
            "special_features": ["Sofá cama disponible", "Cocineta completa", "Vista espectacular", "Dos pisos"]
        }
    
    # Construir respuesta personalizada
    response = f"""🌟 **¡Excelente elección para tu escapada!**

🏠 **MI RECOMENDACIÓN PERSONALIZADA:**
• **Domo {base_recommendation['domo']}** - {base_recommendation['reason']}
• **Capacidad:** {base_recommendation['capacity']}
• **Precio:** {base_recommendation['price']}

✨ **PERFECTO PARA TI PORQUE:**"""
    
    for feature in base_recommendation['special_features']:
        response += f"\n• {feature}"
    
    response += f"""

🌿 **INCLUYE SIN COSTO ADICIONAL:**
• Desayuno gourmet continental
• WiFi de alta velocidad gratuito
• Parqueadero privado y seguro
• Acceso a senderos naturales
• Kit de bienvenida premium

🎯 **EXPERIENCIAS ADICIONALES RECOMENDADAS:**
• Caminata ecológica - $25.000/persona
• Observación de estrellas nocturna - $30.000/persona
• Masaje relajante - $80.000/sesión"""
    
    if is_couple:
        response += "\n• Cena romántica bajo estrellas - $120.000/pareja"
    
    response += f"""

📞 **CONTACTO DIRECTO:**
WhatsApp: +57 305 461 4926

💬 **Para consultar fechas:**
• Escribe "disponibilidad" seguido de tu fecha preferida

¡Estoy aquí para ayudarte a planificar tu experiencia perfecta! 🌙✨"""
    
    return response


def handle_intelligent_recommendations(user_input: str, user_state: dict, memory, qa_chains,
                                     initialize_agent_safe_func, run_agent_safe_func, 
                                     save_user_memory_func, user_id: str) -> Tuple[bool, str]:
    """
    Maneja solicitudes de recomendación usando LLM como herramienta de lógica de negocio
    
    Args:
        user_input: Mensaje del usuario
        user_state: Estado de conversación actual
        memory: Memoria de la conversación
        qa_chains: Cadenas RAG disponibles
        initialize_agent_safe_func: Función para inicializar agente LLM
        run_agent_safe_func: Función para ejecutar agente LLM
        save_user_memory_func: Función para guardar memoria
        user_id: ID del usuario
        
    Returns:
        Tuple[bool, str]: (manejado, respuesta)
    """
    try:
        # Solo procesar si el usuario no está en ningún flujo específico
        if user_state.get("current_flow") != "none":
            return False, ""
        
        # Crear servicio de recomendaciones  
        from services.recommendation_service import create_recommendation_service
        recommendation_service = create_recommendation_service(qa_chains)
        
        # PASO 1: Detectar intención de recomendación
        if not recommendation_service.detect_recommendation_intent(user_input):
            return False, ""
        
        logger.info(f"Procesando solicitud de recomendación inteligente", 
                   extra={"component": "conversation_service", "user_input": user_input[:50]})
        
        # PASO 2: Crear función wrapper para el LLM con manejo robusto de errores
        def llm_agent_wrapper(prompt: str) -> str:
            """Wrapper que adapta la función del agente LLM con fallback inteligente"""
            try:
                # Inicializar agente si es necesario
                init_success, agent, init_error = initialize_agent_safe_func([], memory, max_retries=2)
                if not init_success:
                    raise Exception(f"No se pudo inicializar el agente LLM: {init_error}")
                
                # Ejecutar el agente con el prompt construido
                run_success, result, run_error = run_agent_safe_func(agent, prompt, user_id)
                
                if run_success:
                    if isinstance(result, dict) and "output" in result:
                        return result["output"]
                    elif isinstance(result, str):
                        return result
                    else:
                        return str(result)
                else:
                    # En lugar de fallar, generar una respuesta basada en el contexto
                    if "429" in str(run_error) or "quota" in str(run_error).lower() or "rate limit" in str(run_error).lower():
                        logger.warning("OpenAI quota exceeded - using template-based recommendation")
                        return generate_template_recommendation(user_input, qa_chains)
                    else:
                        raise Exception(f"Error ejecutando agente: {run_error}")
                    
            except Exception as e:
                logger.error(f"Error crítico en LLM wrapper: {e}")
                # Último recurso: generar recomendación basada en templates
                return generate_template_recommendation(user_input, qa_chains)
        
        # PASO 3: Procesar solicitud de recomendación
        handled, response = recommendation_service.process_recommendation_request(
            user_input, llm_agent_wrapper
        )
        
        if handled and response:
            # Agregar a memoria y guardar
            add_message_to_memory(memory, user_input, response)
            save_user_memory_func(user_id, memory)
            
            logger.info("Recomendación inteligente procesada exitosamente", 
                       extra={"component": "conversation_service"})
            
            return True, response
        else:
            logger.warning("No se pudo generar recomendación inteligente")
            return False, ""
            
    except Exception as e:
        logger.error(f"Error en handle_intelligent_recommendations: {e}", 
                    extra={"component": "conversation_service"})
        return False, ""


def handle_continuation_response(user_message: str, user_state: dict, previous_context: str) -> str:
    """Maneja respuestas de continuación basado en contexto previo"""
    if user_message.lower().strip() in ['sí', 'si', 'yes']:
        # Continuar con el contexto anterior
        if previous_context == 'domos_info':
            return "¿Sobre qué domo específico te gustaría saber más?"
        elif previous_context == 'servicios':
            return "¿Qué servicios específicos te interesan?"
        # Agregar más contextos según necesidad
    return None