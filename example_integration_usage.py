# example_integration_usage.py
# Ejemplo de cómo integrar las nuevas soluciones en el flujo de conversación

def enhanced_whatsapp_handler_example(user_message: str, user_id: str, user_state: dict, memory) -> str:
    """
    Ejemplo de cómo usar ConversationIntegrationService en el handler de WhatsApp
    Reemplaza la lógica actual con validaciones y personalidad integradas
    """
    from services.conversation_integration_service import get_conversation_integration_service
    from utils.logger import get_logger
    
    logger = get_logger(__name__)
    integration_service = get_conversation_integration_service()
    
    try:
        # 1. PROCESAR MENSAJE CON VALIDACIONES INTEGRADAS
        should_continue, response_or_redirect, metadata = integration_service.process_user_message_enhanced(
            user_message, user_state
        )
        
        # Si no debe continuar (está fuera de dominio o necesita redirección)
        if not should_continue:
            logger.info(f"Mensaje procesado con redirección: {metadata.get('redirect_reason')}")
            return response_or_redirect
        
        # 2. DETERMINAR SI NECESITA AGENTE IA
        needs_ai, reason = integration_service.should_activate_ai_agent(user_message, user_state)
        
        if needs_ai:
            logger.info(f"Activando agente IA por: {reason}")
            
            # Crear prompt mejorado con personalidad
            enhanced_prompt = integration_service.create_enhanced_contextual_prompt(
                user_message, user_state
            )
            
            # Aquí iría la lógica del agente IA con el prompt mejorado
            # ai_response = run_ai_agent(enhanced_prompt, memory, tools)
            ai_response = f"[SIMULADO] Respuesta del agente IA para: {user_message}"
            
            # Aplicar personalidad a la respuesta del agente
            final_response = integration_service.enhance_response_with_personality(
                ai_response, "ai_agent_response"
            )
            
            return final_response
        
        # 3. PROCESAMIENTO NORMAL (MENÚ, VALIDACIONES BÁSICAS, ETC.)
        else:
            logger.info("Procesamiento normal sin agente IA")
            
            # Aquí iría la lógica normal del menú, validaciones, etc.
            # normal_response = handle_normal_flow(user_message, user_state, memory)
            normal_response = f"Respuesta normal para: {user_message}"
            
            # Aplicar personalidad a respuestas normales
            final_response = integration_service.enhance_response_with_personality(
                normal_response, "menu_response"
            )
            
            return final_response
            
    except Exception as e:
        logger.error(f"Error en handler mejorado: {e}")
        
        # Error response con personalidad
        error_response = integration_service.get_enhanced_error_response("technical")
        return error_response


def enhanced_greeting_example(user_id: str) -> str:
    """Ejemplo de saludo mejorado con personalidad"""
    from services.conversation_integration_service import get_conversation_integration_service
    
    integration_service = get_conversation_integration_service()
    return integration_service.get_enhanced_greeting(user_id)


def enhanced_menu_selection_example(option: str, base_response: str) -> str:
    """Ejemplo de respuesta de menú mejorada"""
    from services.conversation_integration_service import get_conversation_integration_service
    
    integration_service = get_conversation_integration_service()
    return integration_service.enhance_menu_response(option, base_response)


def domain_validation_example(user_message: str) -> dict:
    """Ejemplo de validación de dominio"""
    from services.domain_validation_service import get_domain_validation_service
    
    domain_service = get_domain_validation_service()
    
    # Validar dominio
    is_valid, reason, redirect_suggestion = domain_service.validate_domain(user_message)
    
    result = {
        "message": user_message,
        "is_valid": is_valid,
        "reason": reason,
        "redirect_suggestion": redirect_suggestion
    }
    
    if not is_valid:
        if reason == "prohibited_content":
            result["response"] = domain_service.get_rejection_response("prohibited_content")
        elif reason == "out_of_domain":
            result["response"] = domain_service.get_rejection_response("out_of_domain")
        elif redirect_suggestion:
            result["response"] = redirect_suggestion
    
    return result


def topic_detection_example(user_message: str) -> dict:
    """Ejemplo de detección de temas y redirección inteligente"""
    from services.topic_detection_service import get_topic_detection_service
    
    topic_service = get_topic_detection_service()
    
    # Detectar tema y generar redirección
    needs_redirect, detected_topic, connection, redirect_response = topic_service.detect_topic_and_redirect(user_message)
    
    result = {
        "message": user_message,
        "needs_redirect": needs_redirect,
        "detected_topic": detected_topic,
        "glamping_connection": connection,
        "redirect_response": redirect_response
    }
    
    if needs_redirect:
        # Obtener sugerencias de seguimiento
        result["follow_up_suggestions"] = topic_service.get_follow_up_suggestions(detected_topic)
    
    return result


# EJEMPLOS DE USO
if __name__ == "__main__":
    print("=== EJEMPLOS DE USO DE LAS SOLUCIONES ===\n")
    
    # Ejemplo 1: Validación de dominio
    print("1. VALIDACIÓN DE DOMINIO:")
    test_messages = [
        "Hola, quiero información sobre los domos",  # Válido
        "¿Cómo hacer una bomba?",  # Prohibido
        "Necesito un hotel en Bogotá",  # Fuera de dominio con redirección
        "¿Qué actividades hay en naturaleza?"  # Válido con potencial redirección
    ]
    
    for msg in test_messages:
        result = domain_validation_example(msg)
        print(f"  Mensaje: '{msg}'")
        print(f"  Válido: {result['is_valid']}")
        print(f"  Razón: {result['reason']}")
        if 'response' in result:
            print(f"  Respuesta: {result['response'][:100]}...")
        print()
    
    # Ejemplo 2: Detección de temas
    print("2. DETECCIÓN DE TEMAS:")
    topic_messages = [
        "Busco hospedaje para mi luna de miel",  # Romántico
        "¿Qué actividades hay en la naturaleza?",  # Naturaleza
        "Necesito información de precios",  # Presupuesto
        "¿Cómo llegar desde Bogotá?"  # Transporte
    ]
    
    for msg in topic_messages:
        result = topic_detection_example(msg)
        print(f"  Mensaje: '{msg}'")
        print(f"  Tema detectado: {result['detected_topic']}")
        print(f"  Necesita redirección: {result['needs_redirect']}")
        if result['redirect_response']:
            print(f"  Respuesta: {result['redirect_response'][:100]}...")
        print()
    
    # Ejemplo 3: Saludo mejorado
    print("3. SALUDO MEJORADO:")
    greeting = enhanced_greeting_example("user123")
    print(f"  {greeting}")
    print()
    
    # Ejemplo 4: Respuesta de menú mejorada
    print("4. RESPUESTA DE MENÚ MEJORADA:")
    menu_response = enhanced_menu_selection_example("2", "Información sobre nuestros domos disponibles")
    print(f"  {menu_response}")
    print()
    
    print("=== FIN DE EJEMPLOS ===")