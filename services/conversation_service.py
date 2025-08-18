# Unified conversation service - Eliminates duplication between WhatsApp and Chat endpoints
# This service contains the core conversation logic that was duplicated

from datetime import datetime
from typing import Tuple, Dict, Any, Union
import json
from utils.logger import get_logger, log_conversation, log_error

# Inicializar logger para este módulo
logger = get_logger(__name__)

def add_message_to_memory(memory, user_message: str, ai_response: str):
    """Unified function to add messages to memory with fallback compatibility"""
    try:
        from langchain.schema import HumanMessage, AIMessage
        memory.chat_memory.add_message(HumanMessage(content=user_message))
        memory.chat_memory.add_message(AIMessage(content=ai_response))
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
                                is_menu_selection_func) -> Tuple[bool, Union[str, dict]]:
    """Unified menu selection handling - returns (handled, response)"""
    if is_menu_selection_func(user_message) and user_state["current_flow"] == "none":
        try:
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

def handle_availability_request_unified(user_message: str, user_state: dict, memory, 
                                      handle_availability_request_func, save_user_memory_func, 
                                      user_id: str) -> Tuple[bool, str]:
    """Unified availability request handling - returns (handled, response)"""
    if user_state.get("waiting_for_availability", False) and user_state["current_flow"] == "none":
        try:
            availability_response = handle_availability_request_func(user_message)
            
            # Reset waiting state
            user_state["waiting_for_availability"] = False
            
            # Add to memory
            add_message_to_memory(memory, user_message, availability_response)
            save_user_memory_func(user_id, memory)
            
            return True, availability_response
            
        except Exception as e:
            logger.error(f"Error procesando consulta de disponibilidad: {e}", extra={"phase": "conversation", "component": "availability"})
            user_state["waiting_for_availability"] = False
            error_response = "Disculpa, hubo un error procesando tu consulta. ¿Podrías intentar de nuevo?"
            return True, error_response
    
    return False, ""

def detect_reservation_intent(user_message: str, button_payload: str = None) -> bool:
    """Detect if user wants to make a reservation"""
    message_lower = user_message.lower()
    
    # Check text-based intent
    text_intent = ("reserva" in message_lower and 
                  ("quiero" in message_lower or "hacer" in message_lower or "reservar" in message_lower))
    
    # Check button payload intent
    button_intent = (button_payload and "reserva" in button_payload.lower())
    
    return text_intent or button_intent

def initiate_reservation_flow(user_state: dict, memory, save_user_memory_func, user_id: str) -> str:
    """Initiate reservation flow and return initial message"""
    user_state["current_flow"] = "reserva"
    user_state["reserva_step"] = 1
    user_state["reserva_data"] = {}
    
    initial_message = (
        "¡Claro! Dame los siguientes datos:\n"
        "-Tu nombre completo y de tus acompañantes\n"
        "-Domo que quieras\n"
        "-Fecha que quieras asistir y hasta cuando seria tu estadia (Formato DD/MM/AAAA)\n"
        "-Servicios que quieras incluir\n"
        "-Adicciones (Servicios, mascota etc)\n"
        "-Número de teléfono de contacto\n"
        "-Correo electrónico de contacto\n"
        "-Método de pago preferido (efectivo, transferencia, tarjeta)\n"
        "-Comentarios especiales u observaciones adicionales\n\n"
        "Por favor, escribe toda la información en un solo mensaje."
    )
    
    save_user_memory_func(user_id, memory)
    return initial_message

def process_reservation_step_1(user_message: str, user_state: dict, memory, save_user_memory_func, 
                             user_id: str, parse_reservation_details_func, 
                             validate_and_process_reservation_data_func, 
                             calcular_precio_reserva_func) -> str:
    """Process reservation step 1 (data collection) and return response"""
    
    # Processing message
    processing_msg = "🔄 Procesando tu solicitud de reserva, por favor espera un momento..."
    
    parsed_data = parse_reservation_details_func(user_message)

    if parsed_data:
        validation_success, processed_data, validation_errors = validate_and_process_reservation_data_func(parsed_data, user_id)
        
        if validation_success:
            # Valid data - show reservation confirmation
            user_state["reserva_data"] = processed_data
            
            # Calculate price for confirmation
            fecha_entrada = datetime.fromisoformat(processed_data['fecha_entrada']).date()
            fecha_salida = datetime.fromisoformat(processed_data['fecha_salida']).date()
            
            calculo_precio = calcular_precio_reserva_func(
                domo=processed_data['domo'],
                cantidad_huespedes=processed_data['cantidad_huespedes'],
                fecha_entrada=fecha_entrada,
                fecha_salida=fecha_salida,
                servicios_adicionales=processed_data.get('adicciones', '')
            )
            
            reserva_info = processed_data
            confirmation_msg = (
                "OK: ¡Perfecto! Aquí está el resumen de tu reserva:\n\n"
                f"👥 **Huéspedes:** {', '.join(reserva_info['nombres_huespedes'])} ({reserva_info['cantidad_huespedes']} personas)\n"
                f"🏡 **Domo:** {reserva_info['domo']}\n"
                f"🍽️ **Servicio:** {reserva_info['servicio_elegido']}\n"
                f"➕ **Adiciones:** {reserva_info['adicciones']}\n"
                f"📅 **Entrada:** {datetime.fromisoformat(reserva_info['fecha_entrada']).strftime('%d/%m/%Y')}\n"
                f"📅 **Salida:** {datetime.fromisoformat(reserva_info['fecha_salida']).strftime('%d/%m/%Y')}\n"
                f"📞 **Teléfono:** {reserva_info['numero_contacto']}\n"
                f"📧 **Email:** {reserva_info['email_contacto']}\n"
                f"💰 **Precio Total:** ${calculo_precio['precio_total']:,} COP\n"
                f"💳 **Método de Pago:** {reserva_info.get('metodo_pago', 'No especificado')}\n"
                f"📝 **Comentarios:** {reserva_info.get('comentarios_especiales', 'Ninguno')}\n\n"
                "❓ **¿Confirmas esta reserva?** (Responde: *Sí* o *No*)"
            )

            user_state["reserva_step"] = 2
            save_user_memory_func(user_id, memory)
            return confirmation_msg
            
        else:
            # Validation errors - provide specific feedback
            error_msg = (
                "ERROR: **Encontré algunos problemas con la información proporcionada:**\n\n"
            )
            for i, error in enumerate(validation_errors, 1):
                error_msg += f"{i}. {error}\n"
            
            error_msg += (
                "\n[TIP] **Por favor, envía la información corregida incluyendo:**\n"
                "• Nombres completos de huéspedes\n"
                "• Tipo de domo que deseas\n"
                "• Fechas de entrada y salida (DD/MM/AAAA)\n"
                "• Servicios adicionales que quieras\n"
                "• Adiciones especiales (ej. mascota)\n"
                "• Teléfono de contacto\n"
                "• Email de contacto\n\n"
                "✏️ **Escribe toda la información en un solo mensaje.**"
            )
            
            save_user_memory_func(user_id, memory)
            return error_msg
            
    else:
        # LLM parsing error
        error_msg = (
            "ERROR: **No pude interpretar tu solicitud de reserva.**\n\n"
            "[TIP] **Por favor, asegúrate de incluir toda la información:**\n"
            "• Nombres completos de huéspedes\n"
            "• Tipo de domo que deseas\n"
            "• Fechas de entrada y salida (DD/MM/AAAA)\n"
            "• Servicios adicionales que quieras\n"
            "• Adiciones especiales (ej. mascota)\n"
            "• Teléfono de contacto\n"
            "• Email de contacto\n\n"
            "✏️ **Ejemplo:** \"Juan Pérez y María González, domo Luna, 25/12/2024 hasta 27/12/2024, cena romántica, sin mascotas, 3001234567, juan@email.com\""
        )
        save_user_memory_func(user_id, memory)
        return error_msg

def process_reservation_step_2(user_message: str, user_state: dict, memory, save_user_memory_func, 
                             user_id: str, db, Reserva, calcular_precio_reserva_func, 
                             save_reservation_to_pinecone_func) -> str:
    """Process reservation step 2 (confirmation) and return response"""
    
    if user_message.lower() in ["si", "sí"]:
        try:
            reservation_data = user_state["reserva_data"]
            
            # Convert dates from string to date object
            fecha_entrada = datetime.fromisoformat(reservation_data['fecha_entrada']).date()
            fecha_salida = datetime.fromisoformat(reservation_data['fecha_salida']).date()
            
            # Calculate total reservation price
            calculo_precio = calcular_precio_reserva_func(
                domo=reservation_data['domo'],
                cantidad_huespedes=reservation_data['cantidad_huespedes'],
                fecha_entrada=fecha_entrada,
                fecha_salida=fecha_salida,
                servicios_adicionales=reservation_data.get('adicciones', '')
            )
            
            # Create new reservation in database
            nueva_reserva = Reserva(
                numero_whatsapp=user_id.replace("whatsapp:", ""),
                nombres_huespedes=', '.join(reservation_data['nombres_huespedes']),
                cantidad_huespedes=reservation_data['cantidad_huespedes'],
                domo=reservation_data['domo'],
                fecha_entrada=fecha_entrada,
                fecha_salida=fecha_salida,
                servicio_elegido=reservation_data['servicio_elegido'],
                adicciones=reservation_data['adicciones'],
                numero_contacto=reservation_data['numero_contacto'],
                email_contacto=reservation_data['email_contacto'],
                metodo_pago=reservation_data.get('metodo_pago', 'No especificado'),
                monto_total=calculo_precio['precio_total'],
                comentarios_especiales=reservation_data.get('comentarios_especiales', '')
            )
            
            # Save to database with robust handling
            try:
                db.session.add(nueva_reserva)
                db.session.commit()
                logger.info(f"Reserva guardada en PostgreSQL - ID: {nueva_reserva.id}", extra={"phase": "reservation", "reservation_id": nueva_reserva.id})
                
                pinecone_success = save_reservation_to_pinecone_func(user_id, reservation_data)
                
                success_msg = "🎉 ¡Reserva confirmada y guardada exitosamente!\n\n"
                success_msg += f"📋 **Número de reserva:** {nueva_reserva.id}\n"
                success_msg += f"📅 **Fechas:** {datetime.fromisoformat(reservation_data['fecha_entrada']).strftime('%d/%m/%Y')} - {datetime.fromisoformat(reservation_data['fecha_salida']).strftime('%d/%m/%Y')}\n"
                success_msg += f"👥 **Huéspedes:** {reservation_data['cantidad_huespedes']}\n\n"
                success_msg += "📞 **Nos pondremos en contacto contigo pronto para coordinar los detalles finales.**\n\n"
                success_msg += "✨ **¡Gracias por elegir Glamping Brillo de Luna!**"
                
                if not pinecone_success:
                    success_msg += "\n\nWARNING: *Nota: La reserva se guardó correctamente, pero hubo un problema menor con el sistema de respaldo.*"
                
                return success_msg
                
            except Exception as db_error:
                db.session.rollback()
                logger.error(f"Error al guardar en base de datos: {db_error}", extra={"phase": "reservation", "component": "database"})
                return (
                    "ERROR: **Lo siento, hubo un error al guardar tu reserva.**\n\n"
                    "🔧 **Nuestro sistema técnico está experimentando problemas temporales.**\n\n"
                    "📞 **Por favor:**\n"
                    "• Intenta de nuevo en unos minutos\n"
                    "• O contáctanos directamente por WhatsApp\n"
                    "• Guarda esta conversación como respaldo\n\n"
                    "[TIP] **Tu información está segura y no se perdió.**"
                )
        finally:
            # Reset reservation flow
            user_state["current_flow"] = "none"
            user_state["reserva_step"] = 0
            user_state["reserva_data"] = {}
            save_user_memory_func(user_id, memory)
    else:
        # Reservation cancelled
        user_state["current_flow"] = "none"
        user_state["reserva_step"] = 0
        user_state["reserva_data"] = {}
        save_user_memory_func(user_id, memory)
        return "Reserva cancelada. ¿Hay algo más en lo que pueda ayudarte?"

def process_ai_agent(user_message: str, memory, tools, initialize_agent_safe_func, 
                    run_agent_safe_func, save_user_memory_func, user_id: str) -> str:
    """Process message through AI agent and return response"""
    try:
        # Initialize agent with robust handling
        init_success, custom_agent, init_error = initialize_agent_safe_func(tools, memory, max_retries=3)
        
        if not init_success:
            logger.error(f"Error al inicializar agente: {init_error}", extra={"phase": "conversation", "component": "agent_init"})
            return "Disculpa, nuestro sistema conversacional está experimentando problemas temporales. Por favor, intenta de nuevo en un momento."
        else:
            # Execute agent with robust handling
            run_success, result, run_error = run_agent_safe_func(custom_agent, user_message, max_retries=2)
            
            if run_success:
                agent_answer = result
            else:
                logger.error(f"Error ejecutando agente: {run_error}", extra={"phase": "conversation", "component": "agent_run"})
                
                # Intelligent fallback based on error type
                if "rate limit" in run_error.lower():
                    agent_answer = "[BUSY] Nuestro sistema está un poco ocupado en este momento. Por favor, intenta de nuevo en unos segundos."
                elif "timeout" in run_error.lower():
                    agent_answer = "[TIMEOUT] Tu mensaje está siendo procesado, pero está tomando más tiempo del esperado. ¿Podrías intentar con un mensaje más corto?"
                elif "parsing" in run_error.lower():
                    agent_answer = "[THINKING] Tuve un problema interpretando tu mensaje. ¿Podrías reformularlo de manera más simple?"
                else:
                    agent_answer = "[PROCESSING] Disculpa, tuve un problema procesando tu mensaje. ¿Podrías intentar de nuevo o ser más específico en tu consulta?"
        
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
        
        return agent_answer
        
    except Exception as e:
        logger.error(f"Error inesperado en procesamiento conversacional: {e}", extra={"phase": "conversation", "component": "general"})
        return "🔧 Estamos experimentando problemas técnicos temporales. Por favor, intenta contactarnos de nuevo en unos minutos."

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
        user_states[session_id] = {"current_flow": "none", "reserva_step": 0, "reserva_data": {}, "waiting_for_availability": False}
    
    memory = user_memories[session_id]
    user_state = user_states[session_id]
    response_output = "Lo siento, no pude procesar tu solicitud en este momento."

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
    
    # 2. Handle menu selection
    handled, response = handle_menu_selection_unified(
        user_input, user_state, memory, qa_chains, handle_menu_selection_func, 
        save_user_memory_func, session_id, is_menu_selection_func
    )
    if handled:
        if isinstance(response, dict):
            response_text = response["message"]
        else:
            response_text = response
        return {
            "session_id": session_id,
            "response": response_text,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }

    # 3. Handle availability request
    handled, response = handle_availability_request_unified(
        user_input, user_state, memory, handle_availability_request_func, 
        save_user_memory_func, session_id
    )
    if handled:
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }

    # 4. Handle reservation flow initiation
    if user_state["current_flow"] == "none" and detect_reservation_intent(user_input):
        response = initiate_reservation_flow(user_state, memory, save_user_memory_func, session_id)
        return {
            "session_id": session_id,
            "response": response,
            "memory": messages_to_dict(memory.chat_memory.messages)
        }
    
    # 5. Process reservation step 1 (data collection)
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

    # 6. Process reservation step 2 (confirmation)
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

    # 7. Process through AI agent (default case)
    agent_answer = process_ai_agent(
        user_input, memory, tools, initialize_agent_safe_func, run_agent_safe_func, 
        save_user_memory_func, session_id
    )
    
    return {
        "session_id": session_id,
        "response": agent_answer,
        "memory": messages_to_dict(memory.chat_memory.messages)
    }