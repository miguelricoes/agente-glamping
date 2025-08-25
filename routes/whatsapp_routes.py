# WhatsApp webhook routes for agente glamping
# Extracted from agente.py to improve code organization
# Now uses unified conversation service with performance optimizations

from flask import request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from datetime import datetime
import uuid
import os
import hashlib
import hmac
import time
from collections import defaultdict
from functools import wraps
from utils.logger import get_logger, log_request, log_response, log_error

# PERFORMANCE OPTIMIZATIONS
from services.performance_service import get_performance_optimizer, performance_monitor
from services.async_llm_service import create_async_llm_service, get_global_async_llm_service

# Inicializar logger para este módulo
logger = get_logger(__name__)

def validate_twilio_signature(f):
    """Decorator para validar firma de Twilio con seguridad condicional por entorno"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obtener credenciales de Twilio y configuración de entorno
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        env = os.environ.get('ENV', 'development')

        if not auth_token:
            logger.error("TWILIO_AUTH_TOKEN no configurado")
            return "Unauthorized", 401

        # VALIDACIÓN OBLIGATORIA EN PRODUCCIÓN
        if env == 'production':
            validator = RequestValidator(auth_token)
            correct_url = request.url.replace('http://', 'https://')

            request_valid = validator.validate(
                correct_url,
                request.form,
                request.headers.get('X-Twilio-Signature', '')
            )

            if not request_valid:
                logger.warning(f"🚨 PRODUCCIÓN: Firma Twilio inválida desde {request.remote_addr}")
                logger.warning(f"URL: {correct_url}")
                logger.warning(f"Signature: {request.headers.get('X-Twilio-Signature', 'MISSING')[:20]}...")
                return "Forbidden", 403

        # MODO DESARROLLO CON VALIDACIÓN OPCIONAL
        elif env == 'development':
            skip_validation = os.environ.get('SKIP_TWILIO_VALIDATION', 'false').lower() == 'true'

            if not skip_validation:
                # Validar normalmente en desarrollo también
                validator = RequestValidator(auth_token)
                correct_url = request.url.replace('http://', 'https://')

                request_valid = validator.validate(
                    correct_url,
                    request.form,
                    request.headers.get('X-Twilio-Signature', '')
                )

                if not request_valid:
                    logger.warning(f"🔧 DESARROLLO: Firma Twilio inválida desde {request.remote_addr}")
                    logger.warning(f"URL original: {request.url}")
                    logger.warning(f"URL corregida: {correct_url}")
                    logger.warning(f"Signature header: {request.headers.get('X-Twilio-Signature', 'MISSING')}")
                    logger.warning(f"Form data keys: {list(request.form.keys()) if request.form else 'EMPTY'}")
                    return "Forbidden", 403
            else:
                logger.warning("⚠️ MODO DEBUG: Validación Twilio deshabilitada - SOLO DESARROLLO")

        return f(*args, **kwargs)
    return decorated_function

# Rate limiting simple en memoria (por IP)
request_counts = defaultdict(lambda: {"count": 0, "window_start": time.time()})
RATE_LIMIT_REQUESTS = 10  # requests por ventana
RATE_LIMIT_WINDOW = 60   # 60 segundos

# Cache simple para rate limiting por usuario
user_request_cache = {}
USER_RATE_LIMIT_REQUESTS = 30  # requests per minute per user
USER_RATE_LIMIT_WINDOW = 60   # seconds

def rate_limit(f):
    """Decorator para rate limiting básico"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        current_time = time.time()
        
        # Resetear ventana si ha pasado el tiempo
        if current_time - request_counts[client_ip]["window_start"] > RATE_LIMIT_WINDOW:
            request_counts[client_ip]["count"] = 0
            request_counts[client_ip]["window_start"] = current_time
        
        # Verificar límite
        if request_counts[client_ip]["count"] >= RATE_LIMIT_REQUESTS:
            logger.warning(f"Rate limit excedido para IP {client_ip}")
            return "Rate limit exceeded", 429
        
        # Incrementar contador
        request_counts[client_ip]["count"] += 1
        
        return f(*args, **kwargs)
    return decorated_function

def apply_user_rate_limit(from_number: str) -> bool:
    """Aplicar rate limiting por usuario de WhatsApp"""
    current_time = time.time()

    # Limpiar entradas antiguas
    cutoff_time = current_time - USER_RATE_LIMIT_WINDOW
    user_request_cache[from_number] = [
        req_time for req_time in user_request_cache.get(from_number, [])
        if req_time > cutoff_time
    ]

    # Verificar límite
    user_requests = user_request_cache.get(from_number, [])
    if len(user_requests) >= USER_RATE_LIMIT_REQUESTS:
        return False

    # Agregar request actual
    user_request_cache.setdefault(from_number, []).append(current_time)
    return True

# Import unified conversation service
from services.conversation_service import (
    handle_greeting_new_conversation,
    handle_menu_selection_unified,
    handle_availability_request_unified,
    detect_reservation_intent,
    initiate_reservation_flow,
    process_reservation_step_1,
    process_reservation_step_2,
    process_ai_agent,
    handle_comprehensive_fallback
)

def should_cache_response_check(user_input: str) -> bool:
    """
    Verificar si una consulta de usuario debe buscar en cache
    
    Args:
        user_input: Input del usuario
        
    Returns:
        bool: True si debe verificar cache
    """
    # No buscar en cache para consultas personalizadas o con estado
    personal_patterns = [
        'mi reserva', 'mi solicitud', 'disponibilidad para', 'precio para',
        'confirmar', 'cancelar', 'modificar', 'mi número', 'mi nombre',
        'quiero reservar', 'necesito', 'tengo una pregunta específica'
    ]
    
    input_lower = user_input.lower()
    if any(pattern in input_lower for pattern in personal_patterns):
        return False
    
    # Buscar en cache para consultas informativas generales
    cacheable_patterns = [
        'qué es', 'cómo funciona', 'información sobre', 'cuáles son',
        'política', 'ubicación', 'servicios incluidos', 'actividades',
        'horario', 'contacto', 'preguntas frecuentes', 'faq'
    ]
    
    if any(pattern in input_lower for pattern in cacheable_patterns):
        return True
    
    # Cache también para mensajes informativos largos
    if len(user_input) > 50 and not any(pattern in input_lower for pattern in personal_patterns):
        return True
        
    return False

# SOLUCIÓN 5: Importaciones para nuevas funcionalidades
from services.import_resolver import get_import_resolver
from services.domain_validation_service import get_domain_validation_service
from services.personality_service import get_personality_service

def register_whatsapp_routes(app, db, user_memories, user_states, tools, qa_chains, 
                           load_user_memory, save_user_memory, is_greeting_message,
                           get_welcome_menu, is_menu_selection, handle_menu_selection,
                           handle_availability_request, parse_reservation_details,
                           validate_and_process_reservation_data, calcular_precio_reserva,
                           Reserva, save_reservation_to_pinecone, initialize_agent_safe,
                           run_agent_safe, validation_service=None, availability_service=None):
    """
    Register WhatsApp webhook routes
    
    This function maintains backward compatibility by accepting all dependencies
    that the original whatsapp_webhook function needs from agente.py
    """
    
    def create_contextual_ai_prompt(user_input: str, trigger_type: str, rag_context: str) -> str:
        """Crea prompts específicos usando PromptService optimizado"""
        try:
            from services.prompt_service import get_prompt_service

            prompt_service = get_prompt_service()
            
            # Mapear trigger_type a context_type del PromptService
            context_mapping = {
                "accessibility": "accessibility_needs",
                "images_website": "general",
                "services_included": "general", 
                "services_additional": "activity_focused",
                "reservation_intent": "reservation_intent",
                "price_sensitivity": "price_sensitive",
                "topic_redirect": "general",
                "complex_query": "general"
            }
            
            context_type = context_mapping.get(trigger_type, "general")
            
            # Usar PromptService con contexto adicional
            additional_context = {
                'trigger_type': trigger_type,
                'rag_context': rag_context,
                'auto_activated': True
            }
            
            return prompt_service.get_contextual_prompt(context_type, user_input, additional_context)
            
        except Exception as e:
            logger.error(f"Error creando prompt contextual AI: {e}")
            
            # Fallback a prompt básico optimizado
            return f"""Eres el asistente virtual especializado de Glamping Brillo de Luna en Guatavita, Colombia.

CONTEXTO DETECTADO: {trigger_type}
RAG SUGERIDO: {rag_context}

PERSONALIDAD: Cálido, profesional y entusiasta sobre la experiencia de glamping.

MISIÓN: Proporcionar información precisa y personalizada usando las herramientas RAG disponibles.

Usuario pregunta: {user_input}

Responde de manera completa, útil y con la calidez característica de la hospitalidad colombiana."""

    def process_ai_agent_with_context(contextual_prompt: str, memory, tools, initialize_agent_safe,
                                    run_agent_safe, save_user_memory, user_id: str, rag_context: str):
        """Procesa agente IA con contexto específico"""
        try:
            # Usar el prompt contextual en lugar del mensaje original
            agent_answer = process_ai_agent(
                contextual_prompt, memory, tools, initialize_agent_safe, run_agent_safe,
                save_user_memory, user_id
            )

            logger.info(f"AI agent processed with context: {rag_context}")
            return agent_answer

        except Exception as e:
            logger.error(f"Error processing AI agent with context: {e}")
            return "Disculpa, tuve un problema procesando tu consulta. ¿Podrías reformular tu pregunta?"

    @app.route("/whatsapp_webhook", methods=["POST"])
    @validate_twilio_signature  # AGREGAR decorador de seguridad
    @rate_limit  # AGREGAR rate limiting
    # @performance_monitor  # DESHABILITADO: Causa error LogRecord
    def whatsapp_webhook():
        # VALIDACIÓN DE ENTRADA
        incoming_msg = request.values.get('Body', '').strip()
        from_number = request.values.get('From', '')
        button_payload = request.values.get('ButtonPayload')

        # Validar que tenga contenido básico
        if not from_number:
            logger.warning("Webhook recibido sin número de origen")
            return "Bad Request", 400
        
        # Validar formato del número (básico)
        if not from_number.startswith('whatsapp:+'):
            logger.warning(f"Formato de número inválido: {from_number}")
            return "Bad Request", 400
        
        # Limitar tamaño del mensaje
        if len(incoming_msg) > 1000:
            logger.warning(f"Mensaje demasiado largo ({len(incoming_msg)} chars) de {from_number}")
            incoming_msg = incoming_msg[:1000] + "..."

        # AGREGAR: Verificar rate limiting por usuario
        if not apply_user_rate_limit(from_number):
            logger.warning(f"Rate limit excedido para {from_number}")
            resp = MessagingResponse()
            resp.message("⏳ Has enviado demasiados mensajes. Espera un momento e intenta de nuevo.")
            return str(resp)

        log_request(logger, "/whatsapp_webhook", from_number, incoming_msg)

        resp = MessagingResponse()
        agent_answer = "Lo siento, no pude procesar tu solicitud en este momento."
        
        # PERFORMANCE OPTIMIZATION: TEMPORALMENTE DESHABILITADO (causa error 500)
        # perf_optimizer = get_performance_optimizer()
        perf_optimizer = None
        request_start_time = time.time()
        
        # Generar cache key simplificado
        cache_key = f"whatsapp_webhook:{from_number}:{hash(incoming_msg)}"
        
        # Verificar cache de respuestas primero (para consultas apropiadas)
        # CACHE TEMPORALMENTE DESHABILITADO
        if False:  # should_cache_response_check(incoming_msg):
            cached_response = None  # perf_optimizer.get_cached_response(cache_key)
            if cached_response:
                resp.message(cached_response)
                processing_time = time.time() - request_start_time
                # perf_optimizer.update_performance_metrics(processing_time, was_cached=True)
                logger.info(f"Respuesta servida desde cache para {from_number} ({processing_time:.2f}s)",
                           extra={"user_id": from_number, "cached": True, "processing_time": processing_time})
                return str(resp)

        # Initialize user memory and state
        if from_number not in user_memories:
            user_memories[from_number] = load_user_memory(from_number)
        if from_number not in user_states:
            user_states[from_number] = {
                "current_flow": "none", 
                "reserva_step": 0, 
                "reserva_data": {}, 
                "waiting_for_availability": False,
                "previous_context": "",  # NUEVO
                "last_action": "",       # NUEVO
                "waiting_for_continuation": False  # NUEVO
            }
                
        memory = user_memories[from_number]
        user_state = user_states[from_number]

        # Inicializar servicios una vez al inicio
        resolver = get_import_resolver()
        resolver.initialize_services()

        context_service = resolver.get_service('context_service')
        validation_service = resolver.get_service('validation_service')
        
        # ASEGURAR QUE VALIDATION_SERVICE ESTÉ DISPONIBLE
        if not validation_service:
            from services.validation_service import ValidationService
            validation_service = ValidationService()
            logger.warning("validation_service no estaba disponible, creando nueva instancia")
        
        domain_filter = get_domain_validation_service()
        personality = get_personality_service()

        # 1. FILTRO OUT-OF-DOMAIN CON PROMPT ESPECÍFICO (PRIMERA PRIORIDAD)
        from services.prompt_service import get_prompt_service
        prompt_service = get_prompt_service()

        # Detectar si está fuera del dominio usando método validate_and_redirect
        try:
            needs_redirect, redirect_response = domain_filter.validate_and_redirect(incoming_msg)
            if needs_redirect:
                logger.info(f"Out-of-domain detected for {from_number}, using specialized prompt", 
                           extra={"user_id": from_number, "phase": "domain_filter_advanced"})
                
                # Usar prompt específico para redirección
                out_domain_prompt = prompt_service.get_out_of_domain_prompt(incoming_msg)

                # Procesar con agente usando prompt especializado
                agent_answer = process_ai_agent(
                    out_domain_prompt, memory, tools, initialize_agent_safe, run_agent_safe,
                    save_user_memory, from_number
                )

                enhanced_response = personality.apply_personality_to_response(agent_answer, "redirect")
                resp.message(enhanced_response)
                return str(resp)
        except Exception as e:
            logger.error(f"Error en filtro out-of-domain avanzado: {e}")
            # Continuar con filtro básico si hay error

        # 1.5. FILTRO OUT-OF-DOMAIN BÁSICO (FALLBACK)
        is_valid, reason, redirect_suggestion = domain_filter.validate_domain(incoming_msg)
        if not is_valid:
            if reason == "prohibited_content":
                redirect_response = domain_filter.get_rejection_response("prohibited_content")
            elif reason == "out_of_domain":
                redirect_response = domain_filter.get_rejection_response("out_of_domain")
            elif redirect_suggestion:
                redirect_response = redirect_suggestion
            else:
                redirect_response = domain_filter.get_rejection_response("general")
            
            enhanced_response = personality.apply_personality_to_response(redirect_response, "redirect")
            resp.message(enhanced_response)
            logger.info(f"Out-of-domain filter applied to {from_number}: {reason}", 
                       extra={"user_id": from_number, "filter_reason": reason, "phase": "domain_filter"})
            return str(resp)

        # 2. FALLBACK: Handle specific dome queries without AI (Error 429 prevention)
        dome_response = handle_dome_query_fallback(incoming_msg)
        if dome_response:
            enhanced_response = personality.apply_personality_to_response(dome_response, "information")
            resp.message(enhanced_response)
            logger.info(f"Dome fallback response sent to {from_number}", 
                       extra={"user_id": from_number, "phase": "dome_fallback"})
            return str(resp)

        # 3. Handle greeting in new conversation
        handled, response = handle_greeting_new_conversation(
            memory, incoming_msg, is_greeting_message, get_welcome_menu, save_user_memory, from_number
        )
        if handled:
            enhanced_response = personality.apply_personality_to_response(response, "greeting")
            resp.message(enhanced_response)
            return str(resp)
        
        # 3. Handle continuation of flow with context service
        if user_state.get("waiting_for_continuation", False):
            # Usar context_service para respuestas más inteligentes
            continuation_response = context_service.get_continuation_response(from_number, incoming_msg)
            
            if continuation_response:
                user_state["waiting_for_continuation"] = False
                
                # Guardar contexto de la continuación
                context_service.remember_context(from_number, 'continuation_handled', {
                    'user_input': incoming_msg,
                    'response_type': 'continuation'
                })
                
                resp.message(continuation_response)
                logger.info(f"Continuation response sent to {from_number}", 
                           extra={"user_id": from_number, "response_preview": continuation_response[:100], "phase": "continuation"})
                return str(resp)
            
            # Fallback usando ImportResolver
            conversation_handlers = resolver.get_service('conversation_handlers')
            if conversation_handlers and 'continuation' in conversation_handlers:
                fallback_response = conversation_handlers['continuation'](
                    incoming_msg, user_state, user_state.get("previous_context", "")
                )
                if fallback_response:
                    user_state["waiting_for_continuation"] = False
                    enhanced_response = personality.apply_personality_to_response(fallback_response, "continuation")
                    resp.message(enhanced_response)
                    return str(resp)

        # 4. Handle menu selection (with improved validation service)
        handled, response = handle_menu_selection_unified(
            incoming_msg, user_state, memory, qa_chains, handle_menu_selection, 
            save_user_memory, from_number, is_menu_selection, validation_service
        )
        if handled:
            if isinstance(response, dict):
                resp.message(response["message"])
            else:
                resp.message(response)
            return str(resp)

        # 4.5. Detección específica para nombres de domos (PREVIENE ERROR 429)
        domo_names = ['antares', 'polaris', 'sirius', 'centaury', 'centauro']
        if any(domo_name in incoming_msg.lower() for domo_name in domo_names):
            # Usar respuesta directa sin IA
            domo_response = generate_simple_domo_response(incoming_msg)
            enhanced_response = personality.apply_personality_to_response(domo_response, "information")
            resp.message(enhanced_response)
            logger.info(f"Dome direct response sent to {from_number}", 
                       extra={"user_id": from_number, "phase": "dome_direct"})
            return str(resp)

        # 5. Handle availability request
        handled, response = handle_availability_request_unified(
            incoming_msg, user_state, memory, qa_chains, handle_availability_request, 
            save_user_memory, from_number, validation_service
        )
        if handled:
            resp.message(response)
            return str(resp)

        # 5. Handle reservation flow
        if user_state["current_flow"] == "none" and detect_reservation_intent(incoming_msg, button_payload):
            response = initiate_reservation_flow(user_state, memory, save_user_memory, from_number)
            resp.message(response)
            return str(resp)
        
        # 6. Process reservation step 1 (data collection)
        if user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 1:
            resp.message("🔄 Procesando tu solicitud de reserva, por favor espera un momento...")
            response = process_reservation_step_1(
                incoming_msg, user_state, memory, save_user_memory, from_number,
                parse_reservation_details, validate_and_process_reservation_data, calcular_precio_reserva
            )
            resp.message(response)
            return str(resp)

        # 7. Process reservation step 2 (confirmation)
        if user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 2:
            response = process_reservation_step_2(
                incoming_msg, user_state, memory, save_user_memory, from_number,
                db, Reserva, calcular_precio_reserva, save_reservation_to_pinecone
            )
            resp.message(response)
            return str(resp)

        # 8. Handle website link requests (Variable 1 implementation)
        conversation_handlers = resolver.get_service('conversation_handlers')
        if conversation_handlers and 'website_link' in conversation_handlers:
            handled, link_response = conversation_handlers['website_link'](incoming_msg, validation_service)
            if handled:
                enhanced_response = personality.apply_personality_to_response(link_response, "website")
                resp.message(enhanced_response)
                logger.info(f"Website link response sent to {from_number}", 
                           extra={"user_id": from_number, "response_preview": enhanced_response[:100], "phase": "website_link"})
                return str(resp)

        # 9. Handle admin contact requests (Variable 2 implementation)
        if conversation_handlers and 'admin_contact' in conversation_handlers:
            handled, trigger_type, contact_response = conversation_handlers['admin_contact'](incoming_msg, validation_service)
            if handled:
                enhanced_response = personality.apply_personality_to_response(contact_response, "contact")
                resp.message(enhanced_response)
                logger.info(f"Admin contact response sent to {from_number}", 
                           extra={"user_id": from_number, "response_preview": enhanced_response[:100], "phase": "admin_contact"})
                return str(resp)

        # 10. Handle reservation intent requests (Variable 3 implementation)
        if conversation_handlers and 'reservation_intent' in conversation_handlers:
            handled, reservation_response = conversation_handlers['reservation_intent'](incoming_msg, validation_service, qa_chains)
            if handled:
                enhanced_response = personality.apply_personality_to_response(reservation_response, "reservation_intent")
                resp.message(enhanced_response)
                logger.info(f"Reservation intent response sent to {from_number}", 
                           extra={"user_id": from_number, "response_preview": enhanced_response[:100], "phase": "reservation_intent"})
                return str(resp)

        # 12. Detección inteligente para auto-activación del agente IA
        should_auto_activate, trigger_type, rag_context = validation_service.detect_auto_ai_activation(incoming_msg)

        if should_auto_activate:
            logger.info(f"Auto-activando agente IA para: {trigger_type} con contexto: {rag_context}")

            contextual_prompt = create_contextual_ai_prompt(incoming_msg, trigger_type, rag_context)
            agent_answer = process_ai_agent_with_context(
                contextual_prompt, memory, tools, initialize_agent_safe, run_agent_safe,
                save_user_memory, from_number, rag_context
            )

            # AGREGAR PERSONALIDAD A RESPUESTA DEL AGENTE
            enhanced_agent_answer = personality.apply_personality_to_response(agent_answer, trigger_type)

            if context_service:
                context_service.remember_context(from_number, f'auto_ai_{trigger_type}', {
                    'trigger_type': trigger_type,
                    'rag_context': rag_context,
                    'query': incoming_msg,
                    'response_preview': enhanced_agent_answer[:100]
                })

            resp.message(enhanced_agent_answer)
            return str(resp)

        # 13. Fallback con personalidad (OPTIMIZADO CON ASYNC Y CACHE)
        try:
            # Crear contexto para procesamiento asíncrono
            processing_context = {
                'memory': memory,
                'tools': tools,
                'user_state': user_state,
                'source': 'fallback_general'
            }
            
            # Usar async LLM service si está disponible
            async_llm_service = get_global_async_llm_service()
            if async_llm_service:
                # Procesamiento asíncrono con circuit breaker y fallbacks
                llm_result = async_llm_service.process_message_async(
                    incoming_msg, 
                    from_number,
                    context=processing_context,
                    priority=1,  # Alta prioridad para fallback
                    timeout=20.0  # Timeout agresivo para WhatsApp
                )
                
                if llm_result.get('success') and llm_result.get('response'):
                    agent_answer = llm_result['response']
                    logger.info(f"Async LLM processing successful for {from_number} ({llm_result.get('processing_time', 0):.2f}s)",
                               extra={"user_id": from_number, "source": llm_result.get('source'), "cached": llm_result.get('cached', False)})
                else:
                    # Fallback a procesamiento síncrono
                    logger.warning(f"Async LLM failed, using sync fallback: {llm_result.get('reason', 'unknown')}")
                    agent_answer = process_ai_agent(
                        incoming_msg, memory, tools, initialize_agent_safe, run_agent_safe,
                        save_user_memory, from_number
                    )
            else:
                # Fallback si no hay servicio asíncrono
                agent_answer = process_ai_agent(
                    incoming_msg, memory, tools, initialize_agent_safe, run_agent_safe,
                    save_user_memory, from_number
                )
            
            # AGREGAR PERSONALIDAD A RESPUESTA FINAL
            enhanced_final_answer = personality.apply_personality_to_response(agent_answer, "general")
            
            # PERFORMANCE: Cachear respuesta si es apropiada
            # CACHE DESHABILITADO TEMPORALMENTE
            if False:  # perf_optimizer.should_cache_response(enhanced_final_answer, incoming_msg):
                pass  # perf_optimizer.cache_response(
                # cache_key, 
                # enhanced_final_answer, 
                # ttl=180,  # 3 minutos para respuestas generales
                # metadata={"user_id": from_number, "source": "fallback_general"}
                # )
                # logger.debug(f"Respuesta cacheada para futuras consultas similares")
            
            resp.message(enhanced_final_answer)
            
            # PERFORMANCE: Actualizar métricas
            processing_time = time.time() - request_start_time
            # perf_optimizer.update_performance_metrics(processing_time, was_cached=False)
            
            logger.info(f"WhatsApp respuesta enviada a {from_number} ({processing_time:.2f}s total)", 
                       extra={
                           "user_id": from_number, 
                           "response_preview": enhanced_final_answer[:100], 
                           "phase": "response",
                           "total_processing_time": processing_time
                       })
            return str(resp)
            
        except Exception as e:
            # Error handler con métricas
            processing_time = time.time() - request_start_time
            # perf_optimizer.update_performance_metrics(processing_time, was_cached=False)
            
            logger.error(f"Error crítico en procesamiento final para {from_number}: {e}",
                        extra={"user_id": from_number, "processing_time": processing_time})
            
            # NUEVO: Fallback específico para error 429 (Quota exceeded)
            if "429" in str(e) or "insufficient_quota" in str(e) or "quota" in str(e).lower():
                logger.warning(f"Quota OpenAI excedida, usando respuesta de fallback para {from_number}")
                
                # Usar respuesta de emergencia basada en el tipo de consulta
                fallback_response = generate_fallback_response(incoming_msg, user_state)
                enhanced_response = personality.apply_personality_to_response(fallback_response, "emergency")
                resp.message(enhanced_response)
                return str(resp)
            
            # Respuesta de emergencia genérica para otros errores
            emergency_response = ("Disculpa, estoy experimentando dificultades técnicas. "
                                "Por favor intenta de nuevo en unos momentos o contacta "
                                "directamente a nuestro equipo de soporte.")
            resp.message(emergency_response)
            return str(resp)

def handle_fallback_menu_response(user_message, current_flow):
    """
    Manejar respuestas de menú sin servicios avanzados
    Implementa lógica básica de navegación por menús sin depender de validation_service o IA
    """
    user_msg_lower = user_message.lower().strip()
    
    # Detección básica de opciones de menú
    if any(indicator in user_msg_lower for indicator in ['1', 'uno', 'domo', 'domos', 'habitacion']):
        return generate_simple_menu_response('domos')
    elif any(indicator in user_msg_lower for indicator in ['2', 'dos', 'servicio', 'servicios', 'incluido']):
        return generate_simple_menu_response('servicios')
    elif any(indicator in user_msg_lower for indicator in ['3', 'tres', 'disponibilidad', 'reserva', 'reservar', 'fecha']):
        return generate_simple_menu_response('disponibilidad')
    elif any(indicator in user_msg_lower for indicator in ['4', 'cuatro', 'precio', 'tarifa', 'costo']):
        return generate_simple_menu_response('precios')
    elif any(indicator in user_msg_lower for indicator in ['5', 'cinco', 'ubicacion', 'donde', 'direccion']):
        return generate_simple_menu_response('ubicacion')
    elif any(indicator in user_msg_lower for indicator in ['politica', 'cancelacion', 'reembolso']):
        return generate_simple_menu_response('politicas')
    elif any(indicator in user_msg_lower for indicator in ['contacto', 'ayuda', 'soporte', 'administrador']):
        return generate_simple_menu_response('contacto')
    else:
        # Respuesta de menú principal si no se detecta opción específica
        return generate_simple_menu_response('menu_principal')

def generate_simple_menu_response(menu_option):
    """
    Generar respuestas estáticas para opciones de menú
    Implementa respuestas hardcodeadas para cada opción como backup cuando IA no funciona
    """
    responses = {
        'domos': """🏕️ **NUESTROS DOMOS - BRILLO DE LUNA**

🌟 **Domo Luna** (2 personas)
• Cama king size
• Baño privado con agua caliente
• Terraza privada con vista panorámica
• Desde $280.000/noche

🌟 **Domo Estrella** (4 personas)  
• 2 camas queen
• Baño privado amplio
• Sala de estar
• Terraza con jacuzzi privado
• Desde $450.000/noche

🏔️ Ubicados en las montañas de Boyacá con vistas espectaculares.

¿Te interesa alguno en particular?""",

        'servicios': """✨ **SERVICIOS INCLUIDOS**

🍽️ **Alimentación:**
• Desayuno continental
• Cena gourmet (opcional)

🎯 **Actividades:**
• Senderismo guiado
• Observación de estrellas
• Fogata nocturna
• Juegos de mesa

🛁 **Comodidades:**
• Agua caliente 24/7
• Calefacción
• WiFi en áreas comunes
• Parqueadero privado

🌿 **Experiencias adicionales:**
• Masajes relajantes
• Tours ecológicos
• Workshops de astronomía

¿Qué servicio te interesa más?""",

        'disponibilidad': """📅 **CONSULTA DE DISPONIBILIDAD**

Para consultar disponibilidad necesito:

📋 **Información requerida:**
• Fechas de entrada y salida
• Número de personas
• Tipo de domo preferido

📞 **Contacto directo:**
• WhatsApp: +57 300 123 4567
• Email: reservas@brillodeluna.com

⏰ **Horario de atención:**
• Lunes a Domingo: 8:00 AM - 8:00 PM

Por favor compárteme tus fechas para verificar disponibilidad.""",

        'precios': """💰 **TARIFAS Y PRECIOS**

🏕️ **Domo Luna (2 personas):**
• Temporada baja: $280.000/noche
• Temporada alta: $350.000/noche

🏕️ **Domo Estrella (4 personas):**
• Temporada baja: $450.000/noche  
• Temporada alta: $580.000/noche

📋 **Incluye:**
• Alojamiento
• Desayuno
• Actividades básicas
• Parqueadero

💳 **Formas de pago:**
• Transferencia bancaria
• PSE
• Tarjetas de crédito

¿Necesitas cotización personalizada?""",

        'ubicacion': """📍 **UBICACIÓN - BRILLO DE LUNA**

🗺️ **Dirección:**
Vereda San Isidro, Km 15
Villa de Leyva, Boyacá

🚗 **Cómo llegar:**
• 2.5 horas desde Bogotá
• 15 minutos desde Villa de Leyva
• Coordenadas GPS: 5.6311, -73.5308

🛣️ **Rutas de acceso:**
• Por autopista Norte
• Vía Tunja - Villa de Leyva
• Carretera destapada los últimos 3km

🅿️ Parqueadero privado disponible
📶 Señal de celular limitada

¿Necesitas indicaciones más detalladas?""",

        'politicas': """📋 **POLÍTICAS DE CANCELACIÓN Y RESERVA**

❌ **Cancelaciones:**
• 48+ horas: Reembolso 100%
• 24-48 horas: Reembolso 50%
• Menos de 24h: Sin reembolso

💳 **Reservas:**
• Anticipo: 50% del valor total
• Saldo: Al momento del check-in
• Check-in: 3:00 PM
• Check-out: 12:00 PM

📝 **Requisitos:**
• Documento de identidad
• Depósito de garantía: $100.000
• Máximo ruido hasta 10:00 PM

🚫 **No permitido:**
• Mascotas
• Fumar en domos
• Fiestas o eventos grandes

¿Tienes alguna pregunta específica?""",

        'contacto': """📞 **CONTACTO - BRILLO DE LUNA**

👨‍💼 **Atención al cliente:**
• WhatsApp: +57 300 123 4567
• Teléfono: +57 (8) 732 0456
• Email: info@brillodeluna.com

💼 **Reservas:**
• Email: reservas@brillodeluna.com
• WhatsApp: Este mismo número

⏰ **Horarios:**
• Lunes a Domingo: 8:00 AM - 8:00 PM
• Atención 24/7 para huéspedes

🌐 **Redes sociales:**
• Instagram: @brillodeluna_glamping
• Facebook: Brillo de Luna Glamping

¿En qué más puedo ayudarte?""",

        'menu_principal': """🌙 **BRILLO DE LUNA GLAMPING** 

¡Bienvenido! ¿En qué puedo ayudarte hoy?

1️⃣ Información sobre domos
2️⃣ Servicios incluidos
3️⃣ Consultar disponibilidad  
4️⃣ Precios y tarifas
5️⃣ Ubicación y cómo llegar
📋 Políticas de cancelación
📞 Contacto y soporte

Escribe el número o tema que te interese."""
    }
    
    return responses.get(menu_option, responses['menu_principal'])
def generate_simple_domo_response(message: str) -> str:
    """
    Generar respuestas específicas para consultas de domos sin usar IA
    Previene Error 429 al proporcionar respuestas directas
    """
    message_clean = message.lower().strip()
    
    if 'polaris' in message_clean:
        return """🌟 **DOMO POLARIS** - Experiencia Premium

✨ **Características exclusivas:**
• Capacidad: 2-4 personas
• Cama king size + sofá cama
• Jacuzzi privado con vista panorámica
• Terraza amplia con zona de descanso
• Baño completo con ducha de lluvia
• Calefacción para noches frías

🏔️ **Ubicación privilegiada:**
• Vista 360° a las montañas de Boyacá
• Orientación este para ver el amanecer
• Privacidad total rodeado de naturaleza

💰 **Tarifas Polaris:**
• Temporada baja: $420.000/noche
• Temporada alta: $520.000/noche
• Incluye desayuno y actividades básicas

¿Te gustaría conocer disponibilidad para fechas específicas?"""

    elif 'antares' in message_clean:
        return """⭐ **DOMO ANTARES** - Romance y Naturaleza

✨ **Características especiales:**
• Capacidad: 2 personas (ideal parejas)
• Cama king size ultra confortable
• Mini jacuzzi privado
• Terraza íntima con hamaca
• Baño privado con amenidades premium
• Chimenea para ambiente romántico

🌙 **Experiencia única:**
• Diseño orientado a la observación estelar
• Vista directa a la Vía Láctea
• Ambiente íntimo y privado

💰 **Tarifas Antares:**
• Temporada baja: $350.000/noche
• Temporada alta: $450.000/noche
• Incluye desayuno romántico

¿Quisieras reservar una fecha especial?"""

    elif 'sirius' in message_clean:
        return """🌠 **DOMO SIRIUS** - Confort Familiar

✨ **Características familiares:**
• Capacidad: 4-6 personas
• 2 camas queen + literas
• Jacuzzi familiar amplio
• Terraza grande con zona de juegos
• Baño espacioso con doble lavamanos
• Cocina básica equipada

👨‍👩‍👧‍👦 **Ideal para familias:**
• Espacio amplio y seguro para niños
• Vista a zona de juegos naturales
• Acceso fácil a senderos familiares

💰 **Tarifas Sirius:**
• Temporada baja: $480.000/noche
• Temporada alta: $580.000/noche
• Incluye desayuno familiar

¿Planeas unas vacaciones familiares?"""

    elif 'centaury' in message_clean or 'centauro' in message_clean:
        return """🔥 **DOMO CENTAURY** - Aventura y Comodidad

✨ **Características aventureras:**
• Capacidad: 3-4 personas
• Cama king + cama individual
• Jacuzzi con vista al bosque
• Terraza con zona de fogata privada
• Baño rústico-elegante
• Zona de equipos para trekking

🏃‍♂️ **Para aventureros:**
• Acceso directo a rutas de senderismo
• Zona de equipamiento outdoor
• Vista a cascadas naturales cercanas

💰 **Tarifas Centaury:**
• Temporada baja: $390.000/noche
• Temporada alta: $490.000/noche
• Incluye desayuno energético

¿Listo para tu próxima aventura?"""

    else:
        # Respuesta general si menciona varios domos
        return """🏠 **NUESTROS 4 DOMOS ÚNICOS**

⭐ **ANTARES** (2 pers) - Romance
• Ideal parejas, jacuzzi íntimo
• Desde $350.000/noche

🌟 **POLARIS** (2-4 pers) - Premium  
• Vista 360°, jacuzzi panorámico
• Desde $420.000/noche

🌠 **SIRIUS** (4-6 pers) - Familiar
• Espacioso, perfecto familias
• Desde $480.000/noche

🔥 **CENTAURY** (3-4 pers) - Aventura
• Acceso senderos, zona fogata
• Desde $390.000/noche

🏔️ **Todos incluyen:**
✓ Desayuno gourmet
✓ Jacuzzi privado  
✓ WiFi en áreas comunes
✓ Parqueadero privado

¿Cuál llama más tu atención?"""

def generate_fallback_response(user_input: str, user_state: dict) -> str:
    """Genera respuesta de emergencia cuando OpenAI no está disponible"""
    
    user_input_lower = user_input.lower()
    
    # Respuestas específicas por tipo de consulta
    if any(word in user_input_lower for word in ['domo', 'habitacion', 'alojamiento', 'polaris', 'antares', 'sirius', 'centaury']):
        return """🏕️ **INFORMACIÓN DE DOMOS - BRILLO DE LUNA**

🌟 **Nuestros Domos Disponibles:**
• Antares (2 personas) - Desde $350.000/noche
• Polaris (4 personas) - Desde $480.000/noche
• Sirius (2 personas) - Desde $320.000/noche
• Centaury (4 personas) - Desde $450.000/noche

📍 **Ubicación:** Villa de Leyva, Boyacá
📱 **Reservas:** WhatsApp +57 300 123 4567
🌐 **Web:** www.brillodeluna.com

Disculpa las molestias técnicas. Para información detallada, contáctanos directamente."""

    elif any(word in user_input_lower for word in ['precio', 'costo', 'tarifa']):
        return """💰 **TARIFAS GENERALES**

🏕️ **Rangos de Precios:**
• Domos 2 personas: $320.000 - $380.000/noche
• Domos 4 personas: $450.000 - $520.000/noche

📅 **Varía según:**
• Temporada (alta/baja)
• Días de semana vs fines de semana
• Fechas especiales

📱 **Para cotización exacta:** +57 300 123 4567
🌐 **Consultas online:** www.brillodeluna.com"""

    elif any(word in user_input_lower for word in ['disponibilidad', 'reservar', 'reserva']):
        return """📅 **CONSULTAR DISPONIBILIDAD**

Para verificar disponibilidad y hacer tu reserva:

📱 **WhatsApp Directo:** +57 300 123 4567
📧 **Email:** reservas@brillodeluna.com
🌐 **Formulario Web:** www.brillodeluna.com/reservas

⏰ **Atención:**
• Lunes a Domingo: 8:00 AM - 8:00 PM
• Respuesta inmediata por WhatsApp

Disculpa las molestias técnicas temporales."""

    else:
        return """🌙 **BRILLO DE LUNA GLAMPING**

¡Hola! Estamos experimentando molestias técnicas temporales.

📱 **Contacto Directo:** +57 300 123 4567
🌐 **Website:** www.brillodeluna.com
📧 **Email:** info@brillodeluna.com

**Ubicación:** Villa de Leyva, Boyacá
**Especialidad:** Glamping de lujo con vista panorámica

Te atenderemos personalmente para resolver todas tus dudas."""

    return app